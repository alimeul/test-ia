import { useState } from "react";

function GuessForm({ onGuess, essaisRestants }) {
  const [value, setValue] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [sending, setSending] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!value.trim() || sending) return;

    setSending(true);
    setFeedback(null);
    try {
      const resultat = await onGuess(value.trim());
      if (resultat.gagne) {
        setFeedback({ type: "win", text: "Bravo ! Tous les mots du titre sont révélés !" });
      } else if (resultat.mot_revele) {
        const titleFound = resultat.mots_titre_trouves?.length > 0 &&
          resultat.mots_titre?.includes(resultat.mot_revele);
        const msg = titleFound
          ? `« ${resultat.mot_revele} » fait partie du titre !`
          : `« ${resultat.mot_revele} » révélé dans le texte !`;
        setFeedback({ type: "reveal", text: msg });
      } else {
        setFeedback({ type: "miss", text: `« ${value.trim()} » n'est pas dans l'article.` });
      }
      if (!resultat.gagne && resultat.essais_restants !== undefined && resultat.essais_restants <= 1) {
        setFeedback((prev) => ({
          ...prev,
          text: prev.text + " Plus d'essais !",
        }));
      }
      setValue("");
    } catch (e) {
      setFeedback({ type: "error", text: e.message });
    } finally {
      setSending(false);
    }
  }

  return (
    <form className="guess-form" onSubmit={handleSubmit}>
      <label htmlFor="guess-input" className="sr-only">
        Proposer un mot de l'article
      </label>
      <input
        id="guess-input"
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Proposer un mot…"
        disabled={sending}
        autoComplete="off"
      />
      <button type="submit" className="btn btn-guess" disabled={sending || !value.trim()}>
        {sending ? "…" : "Proposer"}
      </button>
      {feedback && (
        <p className={`feedback feedback-${feedback.type}`} role="alert" aria-live="assertive">
          {feedback.text}
        </p>
      )}
    </form>
  );
}

export default GuessForm;
