import React, { useState } from "react";
import { Globe, Caret, Image, Poll, Emoji, Calendar, Location } from "./icons.jsx";
import { api } from "../lib/api.js";
import { TECH_LABELS, CHIP, sourceLabel, confidenceText } from "../lib/infoshield.js";

const TOOL_ICONS = [Image, Poll, Emoji, Calendar, Location];

// Compact animated shield, matching the extension badge.
function ShieldDot() {
  return (
    <span className="relative shrink-0 grid place-items-center w-9 h-9">
      <span className="absolute inset-1 rounded-full bg-violet-400/40 animate-ping" />
      <span className="relative w-8 h-8 rounded-full bg-white border-2 border-violet-400 grid place-items-center shadow-[0_0_14px_rgba(124,58,237,0.4)]">
        <img src="/badge.png" alt="" className="w-4 h-4 rounded-full" />
      </span>
    </span>
  );
}

// Live, never cached: the composer checks the user's OWN draft. Step 1 explains
// why it was flagged; step 2 (opt-in) offers a respectful rewrite the user may
// apply. The InfoShield UI only appears once the page is activated and the
// Insights toggle is on.
export default function Composer({ activated = false, visible = true }) {
  const [draft, setDraft] = useState("");
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState(null); // { flagged, classification, analysis }
  const [checkedText, setCheckedText] = useState(""); // draft already analyzed
  const [rephrasing, setRephrasing] = useState(false);
  const [suggestion, setSuggestion] = useState("");
  const [expanded, setExpanded] = useState(true);
  const [error, setError] = useState("");

  function clearAnalysis() {
    setResult(null);
    setSuggestion("");
    setError("");
  }

  function onDraftChange(value) {
    setDraft(value);
    // A changed draft invalidates a previous analysis.
    if (value.trim() !== checkedText && (result || suggestion || error)) clearAnalysis();
  }

  async function check() {
    const text = draft.trim();
    if (!text) return;
    clearAnalysis();
    setSuggestion("");
    setExpanded(true);
    setChecking(true);
    try {
      const data = await api.analyzeText(text);
      setResult(data);
      setCheckedText(text);
    } catch (e) {
      setError(e.message || "Could not reach InfoShield on http://localhost:5050.");
    } finally {
      setChecking(false);
    }
  }

  async function suggestAlternative() {
    setRephrasing(true);
    try {
      const rp = await api.rephrase(draft.trim());
      setSuggestion(rp.rephrased || "");
    } catch {
      setError("Could not prepare an alternative.");
    } finally {
      setRephrasing(false);
    }
  }

  function useSuggestion() {
    if (!suggestion) return;
    setDraft(suggestion); // only applied because the user explicitly chose it
    setResult(null);
    setSuggestion("");
    setCheckedText("");
  }

  const analysis = result?.analysis;
  const flagged = result?.flagged;
  const showInfoShield = activated && visible;
  const checkDisabled = checking || !draft.trim() || draft.trim() === checkedText;

  return (
    <div className="px-4 py-3 border-b border-line">
      <div className="flex gap-3">
        <div className="shrink-0 w-11 h-11 rounded-full bg-brand-600 grid place-items-center text-white font-semibold">
          Y
        </div>
        <div className="min-w-0 flex-1">
          <button className="inline-flex items-center gap-1 rounded-full border border-brand-300 text-brand-600 text-[13px] font-semibold px-2.5 py-0.5 mb-2">
            <Globe size={14} /> Everyone <Caret size={14} />
          </button>

          <textarea
            value={draft}
            onChange={(e) => onDraftChange(e.target.value)}
            placeholder="What's happening?"
            rows={2}
            className="w-full resize-none bg-transparent text-[19px] text-ink placeholder:text-muted/70 outline-none py-1"
          />

          {showInfoShield && error && <p className="mt-1 text-[13px] text-rose-500">{error}</p>}

          {/* Analysis UI (hidden when deactivated or toggled off) */}
          {showInfoShield && result && !flagged && (
            <div className="mt-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-[13.5px] text-emerald-800">
              ✓ InfoShield found no manipulation or hate — your post looks clear.
            </div>
          )}

          {showInfoShield && result && flagged && analysis && (
            <div className="mt-2">
              {/* Status row */}
              <div className="flex items-center gap-3 rounded-2xl border border-violet-200 bg-violet-50 px-3 py-2">
                <ShieldDot />
                <span className="text-[13.5px] text-ink/70">{confidenceText(result.classification.confidence)}</span>
                <button
                  onClick={() => setExpanded((v) => !v)}
                  className="ml-auto text-[13px] font-semibold text-violet-600"
                >
                  {expanded ? "Hide" : "What's this?"}
                </button>
              </div>

              {/* Step 1: techniques panel only */}
              {expanded && (
                <div className="mt-2 rounded-2xl border border-violet-100 bg-violet-50/60 p-3">
                  <div className="text-[12px] text-muted mb-2">Your draft uses</div>
                  <div className="flex flex-wrap gap-2">
                    {(analysis.techniques || []).map((t) => (
                      <span
                        key={t}
                        className={`rounded-full border text-[12px] font-semibold px-3 py-1 ${CHIP[t] || "text-violet-600 border-violet-200 bg-violet-50"}`}
                      >
                        {TECH_LABELS[t] || t}
                      </span>
                    ))}
                  </div>

                  {analysis.explanation && (
                    <p className="mt-2.5 text-[13.5px] text-ink/80 leading-snug">{analysis.explanation}</p>
                  )}

                  {analysis.citations?.length > 0 && (
                    <div className="mt-2 text-[12px] text-muted flex items-center flex-wrap gap-1.5">
                      <span className="font-medium text-ink/70">Sources:</span>
                      {analysis.citations.map((u, i) => (
                        <React.Fragment key={u}>
                          <a href={u} target="_blank" rel="noopener noreferrer" className="text-violet-700 hover:underline">
                            {sourceLabel(u)}
                          </a>
                          {i < analysis.citations.length - 1 ? " · " : ""}
                        </React.Fragment>
                      ))}
                    </div>
                  )}

                  {/* Step 2: opt-in alternative (never auto-applied) */}
                  {!suggestion ? (
                    <div className="mt-3">
                      <button
                        onClick={suggestAlternative}
                        disabled={rephrasing}
                        className="inline-flex items-center gap-2 rounded-full bg-violet-600 text-white text-[13px] font-semibold px-4 py-1.5 hover:bg-violet-700 disabled:opacity-60"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
                        </svg>
                        {rephrasing ? "Preparing…" : "Suggest a respectful alternative"}
                      </button>
                    </div>
                  ) : (
                    <div className="mt-3 rounded-xl border border-line bg-white p-3">
                      <div className="text-[12px] font-semibold text-violet-700 mb-1">Suggested alternative</div>
                      <p className="text-[13.5px] text-ink/85 leading-snug whitespace-pre-wrap">{suggestion}</p>
                      <div className="mt-2.5 flex gap-2 justify-end">
                        <button
                          onClick={() => setSuggestion("")}
                          className="rounded-full border border-line text-ink text-[13px] font-semibold px-4 py-1.5 hover:bg-gray-50"
                        >
                          Dismiss
                        </button>
                        <button
                          onClick={useSuggestion}
                          className="rounded-full bg-violet-600 text-white text-[13px] font-semibold px-4 py-1.5 hover:bg-violet-700"
                        >
                          Use this version
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="mt-2 flex items-center justify-between border-t border-line pt-2.5">
            <div className="flex items-center gap-1.5 text-brand-600">
              {TOOL_ICONS.map((Icon, i) => (
                <button key={i} className="w-8 h-8 grid place-items-center rounded-full hover:bg-brand-50" tabIndex={-1}>
                  <Icon size={18} />
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              {showInfoShield && (
                <button
                  onClick={check}
                  disabled={checkDisabled}
                  className="rounded-full border border-violet-300 text-violet-700 font-semibold text-[14px] px-4 py-1.5 hover:bg-violet-50 disabled:opacity-50"
                >
                  {checking ? "Checking…" : "Check with InfoShield"}
                </button>
              )}
              <button
                onClick={() => { setDraft(""); clearAnalysis(); setCheckedText(""); }}
                disabled={!draft.trim()}
                className="rounded-full bg-ink text-white font-semibold text-[15px] px-5 py-1.5 disabled:opacity-50"
              >
                Post
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
