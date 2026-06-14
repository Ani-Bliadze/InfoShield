import React from "react";
import { Home, Hash, Bell, Mail, Bookmark, People, Profile, More } from "./icons.jsx";

const ITEMS = [Home, Hash, Bell, Mail, Bookmark, People, Profile];

export default function LeftRail() {
  return (
    <nav className="hidden sm:flex flex-col items-center gap-1 py-3 w-[68px] shrink-0 sticky top-0 h-screen border-r border-line bg-white">
      <a
        href="/"
        className="w-9 h-9 mb-2 rounded-full bg-ink text-white grid place-items-center hover:opacity-90"
        title="Back to InfoShield home"
      >
        <span className="text-lg leading-none">×</span>
      </a>
      {ITEMS.map((Icon, i) => (
        <button
          key={i}
          className="w-11 h-11 rounded-full grid place-items-center text-ink hover:bg-brand-50 hover:text-brand-600 transition-colors"
          tabIndex={-1}
        >
          <Icon size={24} />
        </button>
      ))}
      <button className="w-11 h-11 rounded-full grid place-items-center text-muted bg-gray-100 hover:bg-gray-200 mt-1" tabIndex={-1}>
        <More size={20} />
      </button>
    </nav>
  );
}
