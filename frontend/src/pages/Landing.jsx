import React, { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api.js";

const DEFAULT_TARGET = "http://localhost:5173/social";

function isLocalhost(url) {
  try {
    const h = new URL(url).hostname.toLowerCase();
    return ["localhost", "127.0.0.1", "0.0.0.0", "::1"].includes(h);
  } catch {
    return false;
  }
}

function ArrowUpRight() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 17 17 7M8 7h9v9" />
    </svg>
  );
}

export default function Landing() {
  const [stage, setStage] = useState("intro"); // intro | form | saved
  const [url, setUrl] = useState(DEFAULT_TARGET);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  // Subtle starfield: faint dots at random positions. Split into two layers that
  // drift gently in opposite directions for a little depth. Memoized so they
  // don't re-randomize on every render.
  const layers = useMemo(() => {
    const make = (n) =>
      Array.from({ length: n }, () => ({
        top: Math.random() * 100,
        left: Math.random() * 100,
        size: Math.random() * 4 + 2.5, // 2.5 - 6.5 px
        op: Math.random() * 0.45 + 0.22, // 0.22 - 0.67
        dur: Math.random() * 5 + 4, // 4 - 9 s twinkle
        delay: Math.random() * 6,
      }));
    return [
      { dots: make(60), anim: "isxDriftA 9s" },
      { dots: make(34), anim: "isxDriftB 12s" },
    ];
  }, []);

  useEffect(() => {
    document.title = "InfoShield";
    api.activationTarget().then((cfg) => {
      if (cfg?.target_url) {
        setUrl(cfg.target_url);
        if (cfg.enabled) setStage("saved");
      }
    }).catch(() => {});
  }, []);

  async function activate(e) {
    e?.preventDefault();
    setError("");
    const value = url.trim();
    if (!value.startsWith("http://") || !isLocalhost(value)) {
      setError("Enter a localhost address, for example http://localhost:5173/social");
      return;
    }
    setSaving(true);
    try {
      await api.saveActivationTarget(value, true);
      setStage("saved");
    } catch (err) {
      setError(err.message || "Could not save. Is the backend running on port 5050?");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      className="relative min-h-screen overflow-hidden bg-[#050409] text-white"
      style={{ fontFamily: "'Roboto', system-ui, Arial, sans-serif" }}
    >
      <style>{`
        @keyframes isxDriftA { from { transform: translate3d(0,0,0); } to { transform: translate3d(190px,-220px,0); } }
        @keyframes isxDriftB { from { transform: translate3d(0,0,0); } to { transform: translate3d(-210px,180px,0); } }
        @keyframes isxTwinkle { 0%,100% { opacity: var(--o); } 50% { opacity: calc(var(--o) * 0.3); } }
      `}</style>

      {/* Background: near-black base with a faintly purple core */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(120% 85% at 50% 28%, #181232 0%, #0b0a1b 46%, #050409 100%)",
        }}
      />
      {/* Purple center glow (a touch more purple than the reference) */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(42% 52% at 50% 32%, rgba(139,92,246,0.24) 0%, rgba(124,58,237,0.11) 38%, rgba(139,92,246,0) 70%)",
        }}
      />
      {/* Edge vignette */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(120% 100% at 50% 40%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)",
        }}
      />

      {/* Drifting starfield */}
      {layers.map((layer, li) => (
        <div
          key={li}
          className="absolute -inset-[35%] pointer-events-none"
          style={{ animation: `${layer.anim} ease-in-out infinite alternate` }}
        >
          {layer.dots.map((d, i) => (
            <span
              key={i}
              className="absolute rounded-full bg-white"
              style={{
                top: `${d.top}%`,
                left: `${d.left}%`,
                width: d.size,
                height: d.size,
                opacity: d.op,
                "--o": d.op,
                animation: `isxTwinkle ${d.dur}s ease-in-out ${d.delay}s infinite`,
              }}
            />
          ))}
        </div>
      ))}

      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6 py-16 text-center">
        {/* Logo */}
        <img
          src="/infoshield-logo.png"
          alt="InfoShield"
          className="w-16 h-16 rounded-2xl shadow-[0_8px_40px_rgba(139,92,246,0.22)]"
        />

        {/* Tag pill */}
        <div className="mt-7 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#a78bfa]" />
          <span className="text-[11px] tracking-[0.28em] font-medium text-white/55 uppercase">
            A media literacy layer
          </span>
        </div>

        {/* Headline */}
        <h1 className="mt-8 font-bold leading-[0.95]">
          <span className="block text-5xl sm:text-7xl lg:text-8xl font-bold tracking-[0.01em] text-white">
            CLARITY
          </span>
          <span className="block mt-2 text-5xl sm:text-7xl lg:text-8xl font-bold bg-gradient-to-r from-[#ede9fe] via-[#c4b5fd] to-[#a78bfa] bg-clip-text text-transparent">
            for your feed.
          </span>
        </h1>

        {/* Description */}
        <p className="mt-8 max-w-4xl text-[15px] sm:text-[17px] leading-relaxed text-white/60">
          InfoShield is a browser extension that adds a quiet layer of{" "}
          <span className="italic text-white/80">media literacy</span> to your social feed. It reads
          every post, flags manipulation and hate speech, and shows in plain language{" "}
          <span className="italic text-white/80">how the words are trying to influence you</span>. It
          never hides or removes anything, because the strongest defense against manipulation is
          simply <span className="italic text-white/80">understanding it</span>.
        </p>

        {/* Single activating button / activation flow */}
        {stage === "intro" && (
          <button
            onClick={() => setStage("form")}
            className="group mt-11 inline-flex items-center gap-4 rounded-full border border-white/15 bg-white/[0.04] hover:bg-white/[0.09] backdrop-blur pl-7 pr-2 py-2 transition-colors"
          >
            <span className="text-[12px] tracking-[0.22em] font-semibold text-white/85">ACTIVATE</span>
            <span className="w-10 h-10 rounded-full bg-white text-[#0a1626] grid place-items-center transition-transform group-hover:scale-105">
              <ArrowUpRight />
            </span>
          </button>
        )}

        {stage === "form" && (
          <form onSubmit={activate} className="mt-11 w-full max-w-md">
            <input
              autoFocus
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              spellCheck={false}
              placeholder="Paste your social site URL"
              className="w-full rounded-full border border-white/15 bg-white/[0.05] px-5 py-3 text-[14px] text-center text-white placeholder:text-white/35 outline-none focus:border-[#a78bfa]/50 focus:ring-1 focus:ring-[#a78bfa]/30"
            />
            {error && <p className="mt-3 text-[13px] text-rose-300">{error}</p>}
            <div className="mt-5 flex justify-center">
              <button
                type="submit"
                disabled={saving}
                className="group inline-flex items-center gap-4 rounded-full border border-white/15 bg-white/[0.04] hover:bg-white/[0.09] disabled:opacity-60 pl-7 pr-2 py-2 transition-colors"
              >
                <span className="text-[12px] tracking-[0.22em] font-semibold text-white/85">
                  {saving ? "ACTIVATING" : "ACTIVATE"}
                </span>
                <span className="w-10 h-10 rounded-full bg-white text-[#0a1626] grid place-items-center transition-transform group-hover:scale-105">
                  <ArrowUpRight />
                </span>
              </button>
            </div>
            <p className="mt-4 text-[12px] text-white/35">Localhost addresses only.</p>
          </form>
        )}

        {stage === "saved" && (
          <div className="mt-11 max-w-md">
            <div className="inline-flex items-center gap-2 text-[#a78bfa] text-[14px] font-semibold">
              <span className="w-2 h-2 rounded-full bg-[#a78bfa]" /> InfoShield is active
            </div>
            <p className="mt-3 text-[14px] leading-relaxed text-white/60">
              Watching <span className="font-mono text-[13px] text-white/80 break-all">{url}</span>.
              Return to that page and <span className="italic text-white/85">refresh it</span> to see
              InfoShield at work.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
