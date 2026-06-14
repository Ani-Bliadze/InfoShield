import React from "react";
import { Globe, Caret, Image, Poll, Emoji, Calendar, Location } from "./icons.jsx";

const TOOL_ICONS = [Image, Poll, Emoji, Calendar, Location];

// A plain "what's happening" composer at the top of the feed. It is decorative
// (no analysis): InfoShield overlays are injected by the extension on the posts
// below, never by the site itself.
export default function Composer() {
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
          <div className="text-[19px] text-muted/70 py-1">What's happening?</div>
          <div className="mt-2 flex items-center justify-between border-t border-line pt-2.5">
            <div className="flex items-center gap-1.5 text-brand-600">
              {TOOL_ICONS.map((Icon, i) => (
                <button key={i} className="w-8 h-8 grid place-items-center rounded-full hover:bg-brand-50" tabIndex={-1}>
                  <Icon size={18} />
                </button>
              ))}
            </div>
            <button className="rounded-full bg-ink text-white font-semibold text-[15px] px-5 py-1.5 opacity-90">
              Post
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
