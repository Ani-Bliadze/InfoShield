import React, { useState } from "react";
import { Globe, Caret, Image, Poll, Emoji, Calendar, Location } from "./icons.jsx";
import { api } from "../lib/api.js";

const TOOL_ICONS = [Image, Poll, Emoji, Calendar, Location];

const TECH_LABELS = {
  fear_amplification: "Fear Amplification",
  scapegoating: "Scapegoating",
  us_vs_them: "Us vs. Them",
  dehumanizing_language: "Dehumanizing Language",
  false_urgency: "False Urgency",
  emotional_manipulation: "Emotional Manipulation",
  identity_targeting: "Identity Targeting",
  ad_hominem: "Ad Hominem",
};

const sourceLabel = (url) => {
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

// The composer runs InfoShield LIVE on the user's own draft (never cached):
// it checks the text and can suggest a kinder rephrasing the user may accept.
export default function Composer() {
  const [draft, setDraft] = useState("");
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState(null); // { flagged, classification, analysis }
  const [rephrasing, setRephrasing] = useState(false);
  const [suggestion, setSuggestion] = useState(null); // string
  const [error, setError] = useState("");

  function reset() {
    setResult(null);
    setSuggestion(null);
    setError("");
  }

  async function check() {
    const text = draft.trim();
    if (!text) return;
    reset();
    setChecking(true);
    try {
      setResult(await api.analyzeText(text));
    } catch (e) {
      setError(e.message || "Could not reach InfoShield on http://localhost:5050.");
    } finally {
      setChecking(false);
    }
  }

  async function doRephrase() {
    const text = draft.trim();
    if (!text) return;
    setRephrasing(true);
    setError("");
    try {
      const data = await api.rephrase(text);
      setSuggestion(data.rephrased || text);
    } catch (e) {
      setError(e.message || "Rephrase failed.");
    } finally {
      setRephrasing(false);
    }
  }

  function useSuggestion() {
    if (suggestion) setDraft(suggestion);
    reset();
  }

  const analysis = result?.analysis;
  const flagged = result?.flagged;

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
            onChange={(e) => {
              setDraft(e.target.value);
              if (result || suggestion || error) reset();
            }}
            placeholder="What's happening?"
            rows={2}
            className="w-full resize-none bg-transparent text-[19px] text-ink placeholder:text-muted/70 outline-none py-1"
          />

          {error && <p className="mt-1 text-[13px] text-rose-500">{error}</p>}

          {result && !flagged && (
            <div className="mt-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-[13.5px] text-emerald-800">
              ✓ InfoShield found no manipulation or hate — your post looks clear.
            </div>
          )}

          {result && flagged && analysis && (
            <div className="mt-2 rounded-xl border border-violet-200 bg-violet-50/70 px-3 py-3">
              <div className="flex items-center justify-between">
                <span className="text-[12px] font-semibold text-violet-700">
                  InfoShield · {analysis.severity} severity
                </span>
                <span className="text-[11px] text-muted">{result.classification?.kind}</span>
              </div>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {(analysis.techniques || []).map((t) => (
                  <span key={t} className="rounded-full bg-white border border-violet-200 text-violet-700 text-[11px] px-2 py-0.5">
                    {TECH_LABELS[t] || t}
                  </span>
                ))}
              </div>
              {analysis.explanation && (
                <p className="mt-2 text-[13.5px] text-ink/80 leading-snug">{analysis.explanation}</p>
              )}
              {analysis.bias_check && (
                <p className="mt-2 text-[12px] text-muted">
                  <b className="text-ink/70">Rights check:</b> {analysis.bias_check}
                </p>
              )}
              {analysis.citations?.length > 0 && (
                <p className="mt-1 text-[12px] text-muted">
                  <b className="text-ink/70">Sources:</b>{" "}
                  {analysis.citations.map((u, i) => (
                    <React.Fragment key={u}>
                      <a href={u} target="_blank" rel="noopener noreferrer" className="text-violet-700 hover:underline">
                        {sourceLabel(u)}
                      </a>
                      {i < analysis.citations.length - 1 ? " · " : ""}
                    </React.Fragment>
                  ))}
                </p>
              )}
              {!suggestion && (
                <button
                  onClick={doRephrase}
                  disabled={rephrasing}
                  className="mt-3 rounded-full bg-violet-600 text-white text-[13px] font-semibold px-4 py-1.5 disabled:opacity-60"
                >
                  {rephrasing ? "Rephrasing…" : "Rephrase kindly"}
                </button>
              )}
            </div>
          )}

          {suggestion && (
            <div className="mt-2 rounded-xl border border-line bg-white px-3 py-3">
              <div className="text-[12px] font-semibold text-emerald-700 mb-1">Suggested rephrasing</div>
              <p className="text-[14px] text-ink leading-snug whitespace-pre-wrap">{suggestion}</p>
              <div className="mt-2.5 flex gap-2">
                <button onClick={useSuggestion} className="rounded-full bg-ink text-white text-[13px] font-semibold px-4 py-1.5">
                  Use this
                </button>
                <button onClick={() => setSuggestion(null)} className="rounded-full border border-line text-ink text-[13px] font-semibold px-4 py-1.5">
                  Keep mine
                </button>
              </div>
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
              <button
                onClick={check}
                disabled={checking || !draft.trim()}
                className="rounded-full border border-violet-300 text-violet-700 font-semibold text-[14px] px-4 py-1.5 hover:bg-violet-50 disabled:opacity-50"
              >
                {checking ? "Checking…" : "Check with InfoShield"}
              </button>
              <button
                onClick={() => { setDraft(""); reset(); }}
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
