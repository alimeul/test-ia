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
      if (resultat.correct) {
        setFeedback({ type: "win", text: "Bravo ! C'est la bonne réponse !" });
      } else {
        setFeedback({ type: "miss", text: `Non, ce n'est pas "${value.trim()}".` });
      }
      if (!resultat.correct && essaisRestants <= 1) {
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
        Proposer un titre d'article
      </label>
      <input
        id="guess-input"
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Proposer un titre…"
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
