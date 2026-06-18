import React from "react";
import { TECH_LABELS, CHIP, sourceLabel, confidenceText } from "../lib/infoshield.js";

// The exact animated shield (rings + glow) used by the extension overlay.
// Custom classes (.fs-*) live in index.css so they never collide with the
// extension's own .isx-* styles when both run on the same page locally.
function Shield() {
  return (
    <span className="fs-shield">
      <span className="fs-shield__ring" />
      <span className="fs-shield__ring" />
      <span className="fs-shield__ring" />
      <img className="fs-shield__core" src="/badge.png" alt="InfoShield" />
    </span>
  );
}

// Hosted-mode per-post overlay: a React port of the extension's buildAnalysis
// (collapsed status bar that expands into the educational card). Rendered only
// for flagged posts while the Insights toggle is on (see PostCard).
export default function PostAnalysis({ post, expanded, onToggle }) {
  const analysis = post.analysis;
  const classification = post.classification || {};
  if (!analysis) return null;

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={onToggle}
        className="flex items-center gap-3 w-full text-left rounded-2xl border border-violet-200 bg-violet-50 px-3.5 py-2 hover:bg-violet-100/60 transition-colors"
      >
        <Shield />
        <span className="text-[13.5px] font-medium text-ink/65">
          {confidenceText(classification.confidence)}
        </span>
        <span className="ml-auto text-[13px] font-semibold text-violet-600">
          {expanded ? "Hide" : "What's this?"}
        </span>
      </button>

      {expanded && (
        <div className="mt-2 rounded-2xl border border-violet-100 bg-violet-50/60 p-4">
          <div className="mb-3 text-[13px] font-bold text-violet-700 underline underline-offset-2">
            Why was this flagged?
          </div>

          <div className="flex flex-wrap gap-2">
            {(analysis.techniques || []).map((t) => (
              <span
                key={t}
                className={`rounded-full border text-[12.5px] font-semibold px-3 py-1 ${CHIP[t] || "text-violet-600 border-violet-200 bg-violet-50"}`}
              >
                {TECH_LABELS[t] || t}
              </span>
            ))}
          </div>

          {analysis.explanation && (
            <p className="mt-3 text-[14px] leading-relaxed text-ink/80">{analysis.explanation}</p>
          )}

          {analysis.recommendation && (
            <div className="mt-2.5 text-[13px] leading-snug text-ink/70">{analysis.recommendation}</div>
          )}

          {analysis.bias_check && (
            <div className="mt-2.5 text-[12px] leading-snug text-muted">
              <b className="text-ink/70">Rights check: </b>
              {analysis.bias_check}
            </div>
          )}

          {analysis.citations?.length > 0 && (
            <div className="mt-3 flex flex-wrap items-center gap-1.5 text-[12px] text-muted">
              <b className="text-ink/70">Sources:</b>
              {analysis.citations.map((u) => (
                <a
                  key={u}
                  href={u}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center rounded-full border border-violet-200 bg-white px-2.5 py-0.5 font-semibold text-violet-700 hover:bg-violet-50"
                >
                  {sourceLabel(u)}
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
