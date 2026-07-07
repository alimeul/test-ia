import { useEffect, useState, useCallback } from "react";
import {
  fetchDefi,
  fetchPartie,
  proposerTitre,
  revelerIndice,
} from "./api";
import ArticleView from "./components/ArticleView";
import GuessForm from "./components/GuessForm";
import GameStatus from "./components/GameStatus";
import History from "./components/History";
import Stats from "./components/Stats";
import "./App.css";

const PAGES = { PLAY: "play", HISTORY: "history", STATS: "stats" };

function App() {
  const [page, setPage] = useState(PAGES.PLAY);
  const [defi, setDefi] = useState(null);
  const [defiDate, setDefiDate] = useState(null);
  const [partie, setPartie] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [indicesText, setIndicesText] = useState("");
  const [reponse, setReponse] = useState(null);
  const [motsTitre, setMotsTitre] = useState([]);
  const [motsTitreTrouves, setMotsTitreTrouves] = useState([]);

  const refreshPartie = useCallback(() => {
    fetchPartie(defiDate)
      .then((p) => {
        if (p.mots_titre) setMotsTitre(p.mots_titre);
        if (p.mots_titre_trouves) setMotsTitreTrouves(p.mots_titre_trouves);
        if (p.texte_mis_a_jour) {
          setDefi((prev) => ({ ...prev, texte_caviarde: p.texte_mis_a_jour }));
        }
        setPartie(p);
      })
      .catch(() => {});
  }, [defiDate]);

  function loadDefi(date) {
    setLoading(true);
    setError(null);
    setDefi(null);
    setPartie(null);
    setIndicesText("");
    setReponse(null);
    setMotsTitre([]);
    setMotsTitreTrouves([]);
    setDefiDate(date);

    fetchDefi(date)
      .then((d) => {
        if (d.mots_titre) setMotsTitre(d.mots_titre);
        setDefi(d);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadDefi(null);
  }, []);

  useEffect(() => {
    if (!defi) return;
    refreshPartie();
  }, [defi, refreshPartie]);

  async function handleGuess(mot) {
    const resultat = await proposerTitre(mot, defiDate);
    if (resultat.mots_titre) setMotsTitre(resultat.mots_titre);
    if (resultat.mots_titre_trouves) setMotsTitreTrouves(resultat.mots_titre_trouves);
    if (resultat.texte_mis_a_jour) {
      setDefi((prev) => ({ ...prev, texte_caviarde: resultat.texte_mis_a_jour }));
    }
    if (resultat.gagne) {
      setReponse(resultat.titre ?? null);
    }
    if (resultat.essais_restants === 0 && !resultat.gagne) {
      setReponse(resultat.titre ?? null);
    }
    refreshPartie();
    return resultat;
  }

  async function handleReveler() {
    if (partie?.termine) return;
    const resultat = await revelerIndice(defiDate);
    if (resultat.indice) {
      setIndicesText(
        (prev) => (prev ? `${prev}, ${resultat.indice}` : resultat.indice),
      );
    }
    refreshPartie();
  }

  function handlePlayDate(date) {
    loadDefi(date);
    setPage(PAGES.PLAY);
  }

  const isToday = !defiDate;
  const titreProgress = motsTitre.length > 0
    ? `${motsTitreTrouves.length}/${motsTitre.length}`
    : null;

  return (
    <main className="app">
      <header className="header">
        <h1>Wikidle</h1>
        <nav className="nav" aria-label="Navigation principale">
          <button
            className={`nav-btn${page === PAGES.PLAY ? " active" : ""}`}
            onClick={() => setPage(PAGES.PLAY)}
            aria-current={page === PAGES.PLAY ? "page" : undefined}
          >
            Jouer
          </button>
          <button
            className={`nav-btn${page === PAGES.HISTORY ? " active" : ""}`}
            onClick={() => setPage(PAGES.HISTORY)}
            aria-current={page === PAGES.HISTORY ? "page" : undefined}
          >
            Historique
          </button>
          <button
            className={`nav-btn${page === PAGES.STATS ? " active" : ""}`}
            onClick={() => setPage(PAGES.STATS)}
            aria-current={page === PAGES.STATS ? "page" : undefined}
          >
            Statistiques
          </button>
        </nav>
      </header>

      {page === PAGES.HISTORY && <History onPlayDate={handlePlayDate} />}

      {page === PAGES.STATS && <Stats />}

      {page === PAGES.PLAY && (
        <>
          {loading && <p className="loading">Chargement…</p>}
          {error && <p className="error">{error}</p>}
          {defi && (
            <>
              <p className="defi-date">
                {isToday ? "Défi du jour" : `Défi du ${defiDate}`}
                {defi.difficulte?.score != null && (
                  <span className="difficulty">
                    Difficulté : {Number(defi.difficulte.score).toFixed(1)}/10
                  </span>
                )}
              </p>

              {titreProgress && !partie?.termine && (
                <div className="titre-progress" role="status" aria-live="polite">
                  Mots du titre trouvés : {titreProgress}
                  <div className="titre-bar">
                    <div
                      className="titre-bar-fill"
                      style={{ width: `${(motsTitreTrouves.length / motsTitre.length) * 100}%` }}
                    />
                  </div>
                  <div className="titre-mots">
                    {motsTitre.map((mt) => (
                      <span
                        key={mt}
                        className={`titre-mot${motsTitreTrouves.includes(mt) ? " found" : ""}`}
                      >
                        {motsTitreTrouves.includes(mt) ? mt : "?".repeat(mt.length)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <ArticleView texte={defi.texte_caviarde} />

              {indicesText && (
                <div className="indice-box" aria-live="polite" aria-atomic="true">
                  <strong>Indice :</strong> {indicesText}
                </div>
              )}

              {!partie?.termine && (
                <>
                  <GuessForm onGuess={handleGuess} essaisRestants={partie?.essais_restants ?? 5} />
                  <button
                    className="btn btn-reveal"
                    onClick={handleReveler}
                    disabled={partie && partie.indices_restants <= 0}
                  >
                    Révéler un mot ({partie?.indices_restants ?? defi.nb_indices_disponibles})
                  </button>
                </>
              )}

              {partie?.termine && <GameStatus partie={partie} reponse={reponse} date={defiDate} />}
            </>
          )}
        </>
      )}
    </main>
  );
}

export default App;
