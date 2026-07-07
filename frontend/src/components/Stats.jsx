import { useEffect, useState } from "react";
import { fetchStatsSession } from "../api";

function Stats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatsSession()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="loading">Chargement…</p>;

  return (
    <section className="stats">
      <h2>Mes statistiques</h2>
      {!stats || stats.total_parties === 0 ? (
        <p className="empty">Aucune partie jouée pour le moment.</p>
      ) : (
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-value">{stats.total_parties}</span>
            <span className="stat-label">Parties</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.total_gagnees}</span>
            <span className="stat-label">Gagnées</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.taux_reussite}%</span>
            <span className="stat-label">Réussite</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.serie_actuelle}</span>
            <span className="stat-label">Série en cours</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.meilleure_serie}</span>
            <span className="stat-label">Meilleure série</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.meilleur_score}</span>
            <span className="stat-label">Meilleur score</span>
          </div>
        </div>
      )}
    </section>
  );
}

export default Stats;
