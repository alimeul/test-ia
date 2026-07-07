import { useState } from "react";

function GameStatus({ partie, reponse }) {
  const [copied, setCopied] = useState(false);

  function buildShareText() {
    const score = partie.gagne ? partie.score : "X";
    const attempts = partie.essais_effectues;
    const hints = partie.indices_reveles;
    const emoji = partie.gagne ? ":wikidle_win:" : ":wikidle_lose:";
    return `Wikidle - ${partie.gagne ? "Gagné" : "Perdu"} !\nScore: ${score}\nEssais: ${attempts}\nIndices: ${hints}\n\nwikidle.app`;
  }

  async function handleShare() {
    const text = buildShareText();
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      try {
        await navigator.share({ text });
      } catch {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    }
  }

  return (
    <section className="game-status">
      {partie.gagne ? (
        <div className="result win">
          <h2>Félicitations !</h2>
          <p>Vous avez trouvé la réponse en {partie.essais_effectues} essai{partie.essais_effectues > 1 ? "s" : ""}.</p>
          <p className="score">Score : {partie.score}</p>
        </div>
      ) : (
        <div className="result lose">
          <h2>Perdu !</h2>
          {reponse && <p>La réponse était : <strong>{reponse}</strong></p>}
          <p>Réessayez demain !</p>
        </div>
      )}
      <button className="btn btn-share" onClick={handleShare}>
        {copied ? "Copié !" : "Partager mon résultat"}
      </button>
    </section>
  );
}

export default GameStatus;
