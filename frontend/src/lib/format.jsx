import React from "react";

export function compact(n) {
  if (n == null) return "";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1).replace(/\.0$/, "")}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1).replace(/\.0$/, "")}K`;
  return `${n}`;
}

// Confidence phrasing per spec.
export function confidenceLabel(confidence) {
  const pct = Math.round((confidence || 0) * 100);
  if (confidence >= 0.8) return `Detected with ${pct}% confidence`;
  return `May contain indicators (${pct}% confidence)`;
}

export function severityTone(severity) {
  // Calm, non-alarmist tones only — no red alert styling.
  switch (severity) {
    case "high":
      return { label: "High", dot: "#7c3aed", chip: "bg-brand-100 text-brand-700" };
    case "medium":
      return { label: "Medium", dot: "#8b5cf6", chip: "bg-brand-50 text-brand-600" };
    default:
      return { label: "Low", dot: "#a78bfa", chip: "bg-violet-50 text-brand-500" };
  }
}

// Split `text` into React nodes, wrapping each highlight phrase. Non-overlapping
// matches only; first valid match per phrase wins (mirrors backend validation).
export function renderHighlighted(text, highlights) {
  if (!highlights || highlights.length === 0) return text;
  const lower = text.toLowerCase();
  const spans = [];
  for (const h of highlights) {
    const phrase = (h.phrase || "").toLowerCase();
    if (!phrase) continue;
    const idx = lower.indexOf(phrase);
    if (idx === -1) continue;
    const span = [idx, idx + phrase.length, h];
    if (spans.some(([s, e]) => span[0] < e && s < span[1])) continue;
    spans.push(span);
  }
  spans.sort((a, b) => a[0] - b[0]);

  const out = [];
  let cursor = 0;
  spans.forEach(([start, end, h], i) => {
    if (start > cursor) out.push(text.slice(cursor, start));
    out.push(
      <mark key={i} className="is-highlight" title={h.label}>
        {text.slice(start, end)}
      </mark>
    );
    cursor = end;
  });
  if (cursor < text.length) out.push(text.slice(cursor));
  return out;
}
