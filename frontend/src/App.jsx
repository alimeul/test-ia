import { useEffect, useState } from "react";
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
  const [indice, setIndice] = useState("");

  useEffect(() => {
    fetchDefi()
      .then(setDefi)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!defi) return;
    fetchPartie()
      .then(setPartie)
      .catch(() => {});
  }, [defi]);

  async function handleGuess(titre) {
    const resultat = await proposerTitre(titre);
    setPartie((prev) => ({
      ...prev,
      essais_effectues: (prev?.essais_effectues ?? 0) + 1,
      essais_restants: resultat.essais_restants,
      gagne: resultat.gagne,
      termine: resultat.gagne || resultat.essais_restants === 0,
      score: resultat.gagne
        ? 1000 - (prev?.indices_reveles ?? 0) * 50 - (prev?.essais_effectues ?? 0) * 100
        : 0,
    }));
    return resultat;
  }

  async function handleReveler() {
    if (partie?.termine) return;
    const resultat = await revelerIndice();
    if (resultat.indice) {
      setIndice((prev) => (prev ? `${prev}, ${resultat.indice}` : resultat.indice));
    }
    setPartie((prev) => ({
      ...prev,
      indices_reveles: (prev?.indices_reveles ?? 0) + 1,
      indices_restants: resultat.indices_restants,
    }));
  }

  if (loading) return <main className="app"><p className="loading">Chargement…</p></main>;
  if (error) return <main className="app"><p className="error">{error}</p></main>;
  if (!defi) return <main className="app"><p className="error">Aucun défi disponible</p></main>;

  return (
    <main className="app">
      <header className="header">
        <h1>Wikidle</h1>
        <p className="subtitle">Devinez l'article Wikipédia du jour !</p>
        {defi.difficulte && (
          <span className="difficulty">Difficulté : {defi.difficulte.score?.toFixed(1) ?? "?"}/10</span>
        )}
      </header>

      <ArticleView texte={defi.texte_caviarde} />

      {indice && (
        <div className="indice-box">
          <strong>Indice :</strong> {indice}
        </div>
      )}

      {!partie?.termine && (
        <>
          <GuessForm onGuess={handleGuess} essaisRestants={partie?.essais_restants ?? 5} />
          <button className="btn btn-reveal" onClick={handleReveler} disabled={partie?.indices_restants <= 0}>
            Révéler un mot ({partie?.indices_restants ?? defi.nb_indices_disponibles})
          </button>
        </>
      )}

      {partie?.termine && <GameStatus partie={partie} />}
    </main>
  );
}

export default App;
