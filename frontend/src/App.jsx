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

  const refreshPartie = useCallback(() => {
    fetchPartie(defiDate)
      .then(setPartie)
      .catch(() => {});
  }, [defiDate]);

  function loadDefi(date) {
    setLoading(true);
    setError(null);
    setDefi(null);
    setPartie(null);
    setIndicesText("");
    setReponse(null);
    setDefiDate(date);

    fetchDefi(date)
      .then(setDefi)
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

  async function handleGuess(titre) {
    const resultat = await proposerTitre(titre, defiDate);
    if (resultat.essais_restants === 0 || resultat.gagne) {
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

  return (
    <main className="app">
      <header className="header">
        <h1>Wikidle</h1>
        <nav className="nav">
          <button
            className={`nav-btn${page === PAGES.PLAY ? " active" : ""}`}
            onClick={() => setPage(PAGES.PLAY)}
          >
            Jouer
          </button>
          <button
            className={`nav-btn${page === PAGES.HISTORY ? " active" : ""}`}
            onClick={() => setPage(PAGES.HISTORY)}
          >
            Historique
          </button>
          <button
            className={`nav-btn${page === PAGES.STATS ? " active" : ""}`}
            onClick={() => setPage(PAGES.STATS)}
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

              <ArticleView texte={defi.texte_caviarde} />

              {indicesText && (
                <div className="indice-box">
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
