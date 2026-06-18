import React, { useEffect, useState } from "react";
import LeftRail from "../components/LeftRail.jsx";
import RightSidebar from "../components/RightSidebar.jsx";
import Composer from "../components/Composer.jsx";
import PostCard from "../components/PostCard.jsx";
import { Settings } from "../components/icons.jsx";
import { api } from "../lib/api.js";

function Tabs() {
  return (
    <div className="flex border-b border-line text-[15px]">
      <button className="flex-1 py-3.5 relative font-semibold text-ink hover:bg-gray-50">
        For you
        <span className="absolute bottom-0 left-1/2 -translate-x-1/2 h-1 w-14 rounded-full bg-brand-600" />
      </button>
      <button className="flex-1 py-3.5 text-muted font-medium hover:bg-gray-50">Following</button>
    </div>
  );
}

export default function Social() {
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState(null);
  // Insights stay hidden until the extension reports a real page scan.
  const [scan, setScan] = useState(null);
  // `activated` mirrors the landing-page activation (read-only here). `visible`
  // is the live show/hide toggle for the InfoShield analysis UI (default on).
  const [activated, setActivated] = useState(false);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    document.title = "Home / For you";
    api
      .feed()
      .then((d) => setPosts(d.posts || []))
      .catch(() => setError("Could not reach the feed server on http://localhost:5050."));
    api.activationTarget().then((cfg) => setActivated(!!cfg?.enabled)).catch(() => {});
  }, []);

  // Toggling visibility hides/shows the extension-injected overlays live (CSS in
  // index.css), with no page refresh and without touching the extension.
  useEffect(() => {
    document.body.classList.toggle("isx-hidden", !visible);
    return () => document.body.classList.remove("isx-hidden");
  }, [visible]);

  useEffect(() => {
    // Listen for the extension's scan results (posted via window.postMessage).
    const onMessage = (e) => {
      const m = e.data;
      if (m && m.source === "infoshield" && m.type === "scan") setScan(m.payload);
    };
    window.addEventListener("message", onMessage);
    // Ask any already-running extension to (re)send its latest scan.
    window.postMessage({ source: "infoshield-page", type: "request-scan" }, "*");
    return () => window.removeEventListener("message", onMessage);
  }, []);

  return (
    <div className="min-h-screen bg-white text-ink font-sans">
      <div className="mx-auto max-w-[1280px] flex">
        <LeftRail />

        <main className="flex-1 min-w-0 max-w-[640px] border-x border-line">
          <header className="sticky top-0 z-20 bg-white/85 backdrop-blur border-b border-line">
            <div className="flex items-center justify-between px-4 h-14">
              <h1 className="text-[20px] font-extrabold tracking-tight">Home</h1>
              <button className="w-9 h-9 grid place-items-center rounded-full text-ink hover:bg-brand-50">
                <Settings size={22} />
              </button>
            </div>
            <Tabs />
          </header>

          {error && (
            <div className="m-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-[14px] text-amber-800">
              {error}
            </div>
          )}

          <Composer activated={activated} visible={visible} />
          {posts.map((p) => (
            <PostCard key={p.id} post={p} />
          ))}

          {posts.length === 0 && !error && (
            <div className="p-8 text-center text-muted">Loading feed…</div>
          )}
        </main>

        <RightSidebar scan={scan} visible={visible} onToggle={setVisible} />
      </div>
    </div>
  );
}
