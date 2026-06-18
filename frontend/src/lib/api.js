// Backend base URL. Locally the demo backend runs on localhost:5050. A hosted
// build points at the deployed backend via VITE_API_BASE. ?api=host:port still
// overrides both for one-off setups.
const params = new URLSearchParams(window.location.search);
export const API_BASE =
  params.get("api") || import.meta.env.VITE_API_BASE || "http://localhost:5050";

// Hosted mode: the site simulates the InfoShield extension itself (renders the
// per-post overlays, pre-activates, and the on-page toggle drives them) so a
// single hosted link is testable without installing the extension. Off locally,
// where the real extension does the injection.
export const HOSTED = import.meta.env.VITE_HOSTED === "1";

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
  // Live (never cached): analyze the user's own draft through the full pipeline.
  analyzeText: async (text) => {
    const res = await fetch(`${API_BASE}/analyze-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `analyze failed (${res.status})`);
    return data;
  },
  // Live (never cached): rephrase the draft to remove manipulation/hate.
  rephrase: async (text) => {
    const res = await fetch(`${API_BASE}/rephrase`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `rephrase failed (${res.status})`);
    return data;
  },
};
