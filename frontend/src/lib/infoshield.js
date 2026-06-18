// Shared InfoShield presentation helpers, used by the Composer (live draft
// check) and the hosted-mode per-post overlay (PostAnalysis).

export const TECH_LABELS = {
  fear_amplification: "Fear Amplification",
  scapegoating: "Scapegoating",
  us_vs_them: "Us vs. Them",
  dehumanizing_language: "Dehumanizing Language",
  false_urgency: "False Urgency",
  emotional_manipulation: "Emotional Manipulation",
  identity_targeting: "Identity Targeting",
  ad_hominem: "Ad Hominem",
};

// Per-technique chip colors (matches the extension overlay palette).
export const CHIP = {
  false_urgency: "text-rose-600 border-rose-200 bg-rose-50",
  fear_amplification: "text-amber-600 border-amber-200 bg-amber-50",
  us_vs_them: "text-teal-600 border-teal-200 bg-teal-50",
  scapegoating: "text-amber-600 border-amber-200 bg-amber-50",
  dehumanizing_language: "text-rose-700 border-rose-200 bg-rose-50",
  emotional_manipulation: "text-violet-600 border-violet-200 bg-violet-50",
  identity_targeting: "text-pink-600 border-pink-200 bg-pink-50",
  ad_hominem: "text-slate-600 border-slate-200 bg-slate-50",
};

export const sourceLabel = (url) => {
  try {
    const h = new URL(url).hostname.replace(/^www\./, "");
    if (h.includes("ohchr")) return "OHCHR";
    if (h.includes("unesco")) return "UNESCO";
    if (h.includes("treaties.un")) return "UN Treaty";
    if (h.includes("un.org") || h.includes("digitallibrary.un")) return "UN";
    return h;
  } catch {
    return "source";
  }
};

export const confidenceText = (c) => {
  const pct = Math.round((c || 0) * 100);
  return c >= 0.8 ? `Detected with ${pct}% confidence` : `May contain indicators (${pct}% confidence)`;
};
