import React, { useState } from "react";
import Avatar from "./Avatar.jsx";
import { Verified, Reply, Repost, Heart, Share, More } from "./icons.jsx";
import { compact } from "../lib/format.jsx";
import { API_BASE, HOSTED } from "../lib/api.js";
import PostAnalysis from "./PostAnalysis.jsx";

// Wrap the first occurrence of each highlight phrase (case-insensitive,
// non-overlapping) in a <mark>, mirroring the extension's in-post highlighting.
function highlightNodes(text, phrases) {
  const lower = text.toLowerCase();
  const ranges = [];
  for (const phrase of phrases) {
    const needle = (phrase || "").toLowerCase();
    if (!needle) continue;
    const idx = lower.indexOf(needle);
    if (idx === -1) continue;
    const end = idx + needle.length;
    if (ranges.some((r) => idx < r.end && end > r.start)) continue; // skip overlaps
    ranges.push({ start: idx, end });
  }
  if (!ranges.length) return text;
  ranges.sort((a, b) => a.start - b.start);
  const out = [];
  let pos = 0;
  ranges.forEach((r, i) => {
    if (r.start > pos) out.push(text.slice(pos, r.start));
    out.push(<mark key={i} className="fs-highlight">{text.slice(r.start, r.end)}</mark>);
    pos = r.end;
  });
  if (pos < text.length) out.push(text.slice(pos));
  return out;
}

function Engagement({ e }) {
  const items = [
    [Reply, e?.replies, "hover:text-sky-500"],
    [Repost, e?.reposts, "hover:text-emerald-500"],
    [Heart, e?.likes, "hover:text-rose-500"],
  ];
  return (
    <div className="mt-2.5 flex items-center gap-10 text-muted text-[13px] select-none">
      {items.map(([Icon, n, hover], i) => (
        <span key={i} className={`inline-flex items-center gap-1.5 ${hover} transition-colors`}>
          <Icon size={18} /> {compact(n)}
        </span>
      ))}
      <span className="inline-flex items-center hover:text-brand-600 transition-colors">
        <Share size={18} />
      </span>
    </div>
  );
}

// A feed post. Carries a stable data-post-id so the InfoShield extension can
// find it locally. In hosted mode (no extension) the site renders the analysis
// overlay itself, gated on the Insights toggle (`visible`).
export default function PostCard({ post, visible = true }) {
  const [expanded, setExpanded] = useState(false);
  const showOverlay = HOSTED && visible && post.flagged && !!post.analysis;
  const phrases = showOverlay ? (post.analysis.highlights || []).map((h) => h.phrase) : [];
  const textContent = showOverlay && expanded ? highlightNodes(post.text, phrases) : post.text;

  return (
    <article
      data-post-id={post.id}
      className="relative px-4 py-3 border-b border-line hover:bg-gray-50/40 transition-colors"
    >
      <div className="flex gap-3">
        <Avatar user={post.user} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1 text-[15px]">
            <span className="font-bold text-ink truncate">{post.user.name}</span>
            {post.user.verified && <Verified size={16} className="shrink-0" />}
            <span className="text-muted truncate">@{post.user.handle}</span>
            <span className="text-muted">·</span>
            <span className="text-muted">{post.time}</span>
            <button className="ml-auto text-muted hover:text-brand-600" tabIndex={-1}>
              <More size={18} />
            </button>
          </div>

          <div className="mt-0.5 text-[15px] leading-normal text-ink whitespace-pre-wrap break-words">
            {textContent}
          </div>

          {post.media?.type === "gradient" && (
            <div className="mt-3 h-44 rounded-2xl border border-line bg-gradient-to-br from-emerald-100 via-emerald-50 to-teal-100" />
          )}

          {post.media?.type === "video" && (
            <video
              className="mt-3 w-full rounded-2xl border border-line bg-black"
              src={`${API_BASE}${post.media.src}`}
              autoPlay
              muted
              loop
              playsInline
              controls
            />
          )}

          <Engagement e={post.engagement} />

          {showOverlay && (
            <PostAnalysis post={post} expanded={expanded} onToggle={() => setExpanded((v) => !v)} />
          )}
        </div>
      </div>
    </article>
  );
}
