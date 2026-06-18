import React from "react";
import { Search } from "./icons.jsx";
import { compact } from "../lib/format.jsx";

const TRENDS = [
  { cat: "Trending in Technology", name: "Open Source AI", posts: 42100 },
  { cat: "Trending", name: "#MondayMotivation", posts: 88700 },
  { cat: "Sports · Trending", name: "Champions League", posts: 213400 },
  { cat: "Trending in Science", name: "James Webb", posts: 19200 },
];

const SUGGEST = [
  { name: "MediaWatch", handle: "mediawatch", color: "#0d9488", initial: "M" },
  { name: "City Times", handle: "citytimes", color: "#ea580c", initial: "C" },
];

// Rendered only once the extension reports a real page scan. Before that there
// is nothing on the page that hints at the InfoShield extension.
function InsightsCard({ scan, on, onToggle }) {
  return (
    <div
      className={`rounded-2xl border p-4 transition-colors ${
        on ? "border-violet-200 bg-violet-50 shadow-soft" : "border-line bg-gray-100"
      }`}
    >
      <div className="flex items-center gap-2.5">
        <img src="/badge.png" alt="" className="shrink-0 w-7 h-7 rounded-full" />
        <div className="min-w-0 flex-1">
          <div className={`font-bold text-[15px] ${on ? "text-ink" : "text-ink/70"}`}>InfoShield Insights</div>
          <div className="text-[12px] text-muted">Last 30 min · {scan.scanned} posts scanned.</div>
        </div>
        <button
          type="button"
          aria-label="Toggle InfoShield analysis"
          onClick={() => onToggle((v) => !v)}
          className={`relative shrink-0 w-11 h-6 rounded-full transition-colors ${on ? "bg-violet-600" : "bg-gray-300"}`}
        >
          <span
            className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
              on ? "translate-x-5" : ""
            }`}
          />
        </button>
      </div>

      {on && (
        <div className="mt-4 space-y-2.5">
          <Row label="Posts analyzed" value={scan.scanned} />
          <Row label="Patterns detected" value={scan.patternsDetected} accent />
          <div className="pt-2.5 border-t border-violet-200/70">
            <div className="text-violet-600 text-[13px] font-semibold flex items-center gap-1.5">
              <span>↗</span> Most common pattern
            </div>
            <div className="text-[13px] text-ink/80 mt-0.5">{scan.mostCommonPattern || "—"}</div>
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ label, value, accent }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[14px] text-ink/80">{label}</span>
      <span className={`font-bold text-[16px] ${accent ? "text-orange-500" : "text-violet-600"}`}>
        {value}
      </span>
    </div>
  );
}

export default function RightSidebar({ scan, visible, onToggle }) {
  return (
    <aside className="hidden lg:block w-[350px] shrink-0 pl-8 pr-4 py-3">
      <div className="sticky top-3 space-y-4">
        <label className="flex items-center gap-2 rounded-full bg-gray-100 px-4 py-2.5 text-muted focus-within:bg-white focus-within:ring-1 focus-within:ring-brand-300">
          <Search size={18} />
          <input
            className="bg-transparent outline-none text-[14px] text-ink placeholder:text-muted w-full"
            placeholder="Search"
          />
        </label>

        {scan && <InsightsCard scan={scan} on={visible} onToggle={onToggle} />}

        <div className="rounded-2xl border border-line bg-gray-50/80">
          <h2 className="px-4 pt-3 pb-1 font-bold text-[19px] text-ink">Trends for you</h2>
          {TRENDS.map((t) => (
            <div key={t.name} className="px-4 py-2.5 hover:bg-gray-100/70 cursor-pointer">
              <div className="text-[12px] text-muted">{t.cat}</div>
              <div className="font-bold text-[15px] text-ink leading-tight">{t.name}</div>
              <div className="text-[12px] text-muted">{compact(t.posts)} posts</div>
            </div>
          ))}
          <button className="px-4 py-3 text-brand-600 text-[14px] hover:underline">Show more</button>
        </div>

        <div className="rounded-2xl border border-line bg-gray-50/80">
          <h2 className="px-4 pt-3 pb-1 font-bold text-[19px] text-ink">Who to follow</h2>
          {SUGGEST.map((s) => (
            <div key={s.handle} className="px-4 py-2.5 flex items-center gap-3 hover:bg-gray-100/70">
              <div
                className="w-10 h-10 rounded-full grid place-items-center text-white font-semibold"
                style={{ background: s.color }}
              >
                {s.initial}
              </div>
              <div className="min-w-0 flex-1">
                <div className="font-bold text-[14px] text-ink truncate">{s.name}</div>
                <div className="text-[13px] text-muted truncate">@{s.handle}</div>
              </div>
              <button className="rounded-full bg-ink text-white text-[13px] font-semibold px-4 py-1.5 hover:opacity-90">
                Follow
              </button>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
