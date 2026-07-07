import { useEffect, useState } from "react";
import { fetchHistorique } from "../api";

function History({ onPlayDate }) {
  const [defis, setDefis] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistorique()
      .then(setDefis)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="loading">Chargement…</p>;

  return (
    <section className="history">
      <h2>Défis passés</h2>
      {defis.length === 0 ? (
        <p className="empty">Aucun défi passé.</p>
      ) : (
        <ul className="history-list">
          {defis.map((d) => (
            <li key={d.date} className="history-item">
              <span className="history-date">{d.date}</span>
              <span className="history-difficulty">
                Difficulté : {d.difficulte.toFixed(1)}/10
              </span>
              <button className="btn btn-small" onClick={() => onPlayDate(d.date)}>
                Jouer
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default History;
