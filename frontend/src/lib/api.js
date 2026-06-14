// Backend base URL. The demo backend runs on localhost:5050; override with
// ?api=http://host:port for unusual setups.
const params = new URLSearchParams(window.location.search);
export const API_BASE =
  params.get("api") || "http://localhost:5050";

async function getJSON(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

export const api = {
  feed: () => getJSON("/feed"),
  stats: () => getJSON("/stats"),
  health: () => getJSON("/health"),
  activationTarget: () => getJSON("/activation-target"),
  saveActivationTarget: async (targetUrl, enabled = true) => {
    const res = await fetch(`${API_BASE}/activation-target`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_url: targetUrl, enabled }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `save failed (${res.status})`);
    return data;
  },
  rebuildCache: async () => {
    const res = await fetch(`${API_BASE}/rebuild-cache`, { method: "POST" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `rebuild failed (${res.status})`);
    return data;
  },
};
