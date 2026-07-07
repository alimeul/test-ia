const BASE = "/api/defis";

function sessionId() {
  let id = sessionStorage.getItem("wikidle_session");
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem("wikidle_session", id);
  }
  return id;
}

export { sessionId };

export async function fetchDefi(date) {
  const url = date ? `${BASE}/${date}` : `${BASE}/aujourdhui`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Aucun défi disponible");
  return res.json();
}

export async function fetchPartie(date) {
  const url = date
    ? `${BASE}/${date}/partie?session_id=${sessionId()}`
    : `${BASE}/aujourdhui/partie?session_id=${sessionId()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Impossible de récupérer l'état de la partie");
  return res.json();
}

export async function proposerTitre(titre, date) {
  const url = date
    ? `${BASE}/${date}/proposer?session_id=${sessionId()}`
    : `${BASE}/aujourdhui/proposer?session_id=${sessionId()}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ titre_propose: titre }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Erreur lors de la proposition");
  }
  return res.json();
}

export async function revelerIndice(date) {
  const url = date
    ? `${BASE}/${date}/reveler?session_id=${sessionId()}`
    : `${BASE}/aujourdhui/reveler?session_id=${sessionId()}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Plus d'indices disponibles");
  }
  return res.json();
}

export async function fetchHistorique() {
  const res = await fetch(`${BASE}/historique`);
  if (!res.ok) throw new Error("Impossible de récupérer l'historique");
  return res.json();
}

export async function fetchStatsSession() {
  const res = await fetch(`/api/stats/session?session_id=${sessionId()}`);
  if (!res.ok) throw new Error("Impossible de récupérer les statistiques");
  return res.json();
}
