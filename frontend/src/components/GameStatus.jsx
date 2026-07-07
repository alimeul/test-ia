import { useState } from "react";

function GameStatus({ partie, reponse, date }) {
  const [copied, setCopied] = useState(false);

  function buildGrid() {
    const max = 5;
    const used = partie.essais_effectues;
    const won = partie.gagne;
    const cells = [];
    for (let i = 0; i < used; i++) {
      cells.push(i === used - 1 && won ? "🟩" : "⬛");
    }
    return cells.join("");
  }

  function buildShareText() {
    const dateStr = date ?? new Date().toISOString().slice(0, 10);
    const grid = buildGrid();
    const hints = "🔍".repeat(partie.indices_reveles) || "🔍0";
    const emoji = partie.gagne ? "🎉" : "😞";
    return [
      `Wikidle #${dateStr}`,
      `${emoji} ${partie.gagne ? "Gagné" : "Perdu"} !`,
      `${grid}  ${partie.essais_effectues}/${5}  ${hints}`,
      `Score: ${partie.score}`,
      "",
      "wikidle.app",
    ].join("\n");
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
    <section className="game-status" role="status" aria-live="polite">
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
      <div className="share-preview">
        <pre className="share-text">{buildShareText()}</pre>
      </div>
      <button className="btn btn-share" onClick={handleShare}>
        {copied ? "Copié !" : "Partager mon résultat"}
      </button>
    </section>
  );
}

export default GameStatus;
