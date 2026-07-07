import { useEffect, useState, useCallback } from "react";
import {
  fetchDefi,
  fetchHistorique,
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
  const [propositions, setPropositions] = useState([]);
  const [historique, setHistorique] = useState([]);

  useEffect(() => {
    fetchHistorique().then(setHistorique).catch(() => {});
  }, []);

  const refreshPartie = useCallback(() => {
    fetchPartie(defiDate)
      .then((p) => {
        if (p.mots_titre) setMotsTitre(p.mots_titre);
        if (p.mots_titre_trouves) setMotsTitreTrouves(p.mots_titre_trouves);
        if (p.propositions) setPropositions(p.propositions);
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
    if (resultat.propositions) setPropositions(resultat.propositions);
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

  function goToDate(delta) {
    const idx = historique.findIndex((h) => h.date === (defiDate ?? historique[historique.length - 1]?.date));
    const next = historique[idx + delta];
    if (next) loadDefi(next.date);
  }

  const isToday = !defiDate;
  const titreProgress = motsTitre.length > 0
    ? `${motsTitreTrouves.length}/${motsTitre.length}`
    : null;
  const currentIdx = historique.findIndex((h) => h.date === (defiDate ?? historique[historique.length - 1]?.date));

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
              <div className="date-nav">
                <button
                  className="btn btn-nav"
                  disabled={currentIdx <= 0}
                  onClick={() => goToDate(-1)}
                  aria-label="Jour précédent"
                >
                  ‹
                </button>
                <div className="date-picker">
                  {historique.map((h) => (
                    <button
                      key={h.date}
                      className={`date-dot${h.date === (defiDate ?? historique.at(-1)?.date) ? " active" : ""}`}
                      onClick={() => loadDefi(h.date)}
                      aria-label={`Défi du ${h.date}`}
                      title={h.date}
                    >
                      {h.date.slice(5)}
                    </button>
                  ))}
                </div>
                <button
                  className="btn btn-nav"
                  disabled={currentIdx >= historique.length - 1}
                  onClick={() => goToDate(1)}
                  aria-label="Jour suivant"
                >
                  ›
                </button>
              </div>

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

              <div className="game-area">
                <div className="game-main">
                  <ArticleView texte={defi.texte_caviarde} />
                </div>
                {propositions.length > 0 && (
                  <aside className="word-sidebar" aria-label="Mots proposés">
                    <h3>Mots proposés</h3>
                    <ul className="word-list">
                      {propositions.map((p, i) => (
                        <li key={i} className={`word-item${p.trouve ? " found" : " miss"}`}>
                          <span className="word-text">{p.mot}</span>
                          <span className="word-occ">{p.nb_occurrences > 0 ? `×${p.nb_occurrences}` : "✗"}</span>
                        </li>
                      ))}
                    </ul>
                  </aside>
                )}
              </div>

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
