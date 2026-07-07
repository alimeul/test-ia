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
import "./App.css";

function App() {
  const [defi, setDefi] = useState(null);
  const [partie, setPartie] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [indicesText, setIndicesText] = useState("");
  const [reponse, setReponse] = useState(null);

  const refreshPartie = useCallback(() => {
    fetchPartie()
      .then(setPartie)
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchDefi()
      .then(setDefi)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!defi) return;
    refreshPartie();
  }, [defi, refreshPartie]);

  async function handleGuess(titre) {
    const resultat = await proposerTitre(titre);
    if (resultat.essais_restants === 0 || resultat.gagne) {
      setReponse(resultat.titre ?? null);
    }
    refreshPartie();
    return resultat;
  }

  async function handleReveler() {
    if (partie?.termine) return;
    const resultat = await revelerIndice();
    if (resultat.indice) {
      setIndicesText(
        (prev) => (prev ? `${prev}, ${resultat.indice}` : resultat.indice),
      );
    }
    refreshPartie();
  }

  if (loading) return <main className="app"><p className="loading">Chargement…</p></main>;
  if (error) return <main className="app"><p className="error">{error}</p></main>;
  if (!defi) return <main className="app"><p className="error">Aucun défi disponible</p></main>;

  return (
    <main className="app">
      <header className="header">
        <h1>Wikidle</h1>
        <p className="subtitle">Devinez l'article Wikipédia du jour !</p>
        {defi.difficulte?.score != null && (
          <span className="difficulty">
            Difficulté : {Number(defi.difficulte.score).toFixed(1)}/10
          </span>
        )}
      </header>

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

      {partie?.termine && <GameStatus partie={partie} reponse={reponse} />}
    </main>
  );
}

export default App;
