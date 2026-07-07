const BASE = "/api/defis";

function sessionId() {
  let id = sessionStorage.getItem("wikidle_session");
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem("wikidle_session", id);
  }
  return id;
}

export async function fetchDefi() {
  const res = await fetch(`${BASE}/aujourdhui`);
  if (!res.ok) throw new Error("Aucun défi disponible");
  return res.json();
}

export async function fetchPartie() {
  const res = await fetch(`${BASE}/aujourdhui/partie?session_id=${sessionId()}`);
  if (!res.ok) throw new Error("Impossible de récupérer l'état de la partie");
  return res.json();
}

export async function proposerTitre(titre) {
  const res = await fetch(`${BASE}/aujourdhui/proposer?session_id=${sessionId()}`, {
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

export async function revelerIndice() {
  const res = await fetch(`${BASE}/aujourdhui/reveler?session_id=${sessionId()}`, {
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
