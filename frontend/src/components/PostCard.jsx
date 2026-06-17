import React from "react";
import Avatar from "./Avatar.jsx";
import { Verified, Reply, Repost, Heart, Share, More } from "./icons.jsx";
import { compact } from "../lib/format.jsx";
import { API_BASE } from "../lib/api.js";

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

// A plain feed post. Carries a stable data-post-id so the InfoShield extension
// can find it; the site itself never renders analysis (extension-driven demo).
export default function PostCard({ post }) {
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
            {post.text}
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
        </div>
      </div>
    </article>
  );
}
