/* InfoShield content script.
 *
 * Activates ONLY when:
 *   - the global on/off toggle (chrome.storage.local) is enabled, AND
 *   - the current page matches the landing-page-selected target URL
 *     (read from the backend's activation config).
 *
 * It finds posts via [data-post-id], fetches author-agnostic analysis from the
 * backend, and injects a self-contained, prefixed overlay (badge + educational
 * card). It never hides, blurs, or removes content. Fails silently if the
 * backend is unavailable.
 */
(() => {
  "use strict";

  const BACKEND = "http://localhost:5050";
  const DEBUG = false; // flip to true to trace activation/injection in the page console
  const dlog = (...a) => DEBUG && console.log("[InfoShield]", ...a);
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

  const STATE = {
    active: false,
    target: "",
    analyses: new Map(), // post_id -> {classification, analysis, flagged}
    flagged: new Set(),  // post ids we injected
    observer: null,
  };

  const badgeUrl = chrome.runtime.getURL("icons/badge.png");

  const normalize = (u) => {
    try {
      const x = new URL(u);
      return `${x.protocol}//${x.hostname}:${x.port || ""}${x.pathname}`.replace(/\/$/, "").toLowerCase();
    } catch {
      return "";
    }
  };

  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };

  const confidenceLabel = (c) => {
    const pct = Math.round((c || 0) * 100);
    return c >= 0.8 ? `Detected with ${pct}% confidence` : `May contain indicators (${pct}% confidence)`;
  };

  // ---- backend ----------------------------------------------------------
  async function getEnabled() {
    return new Promise((res) =>
      chrome.storage.local.get(["enabled"], (r) => res(r.enabled !== false))
    );
  }

  async function fetchJSON(path) {
    const res = await fetch(`${BACKEND}${path}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`${path} ${res.status}`);
    return res.json();
  }

  // ---- highlighting (generic, reversible) -------------------------------
  function highlightIn(node, phrases, on) {
    // Remove existing marks first.
    node.querySelectorAll("mark.isx-highlight").forEach((m) => {
      const t = document.createTextNode(m.textContent);
      m.replaceWith(t);
    });
    node.normalize();
    if (!on) return;

    for (const phrase of phrases) {
      const needle = (phrase || "").toLowerCase();
      if (!needle) continue;
      const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT, {
        acceptNode: (tn) =>
          tn.parentElement && tn.parentElement.closest(".isx-wrap")
            ? NodeFilter.FILTER_REJECT
            : NodeFilter.FILTER_ACCEPT,
      });
      let tn;
      let done = false;
      while (!done && (tn = walker.nextNode())) {
        const idx = tn.nodeValue.toLowerCase().indexOf(needle);
        if (idx === -1) continue;
        const after = tn.splitText(idx);
        after.splitText(needle.length);
        const mark = el("mark", "isx-highlight");
        mark.textContent = after.nodeValue;
        after.replaceWith(mark);
        done = true;
      }
    }
  }

  // ---- overlay construction --------------------------------------------
  function buildBadge() {
    const wrap = el("span", "isx-badge");
    wrap.title = "Flagged by InfoShield";
    for (let i = 0; i < 3; i++) wrap.appendChild(el("span", "isx-ring"));
    const img = el("img", "isx-badge__core");
    img.src = badgeUrl;
    img.alt = "InfoShield";
    wrap.appendChild(img);
    return wrap;
  }

  function buildAnalysis(node, entry) {
    const { classification, analysis } = entry;
    const wrap = el("div", "isx-wrap");
    let expanded = false;
    let highlightsOn = false;

    const bar = el("button", "isx-bar");
    const bimg = el("img");
    bimg.src = badgeUrl;
    bar.appendChild(bimg);
    bar.appendChild(el("span", "isx-bar__name", "InfoShield"));
    bar.appendChild(el("span", "isx-bar__conf", `· ${confidenceLabel(classification.confidence)}`));
    const more = el("span", "isx-bar__more");
    const moreText = el("span", null, "What's this?");
    more.appendChild(moreText);
    bar.appendChild(more);
    wrap.appendChild(bar);

    const card = el("div", "isx-card");
    card.style.display = "none";

    const head = el("div", "isx-card__head");
    const himg = el("img");
    himg.src = badgeUrl;
    head.appendChild(himg);
    head.appendChild(el("div", "isx-card__title", "Manipulation techniques detected"));
    const sev = el("span", "isx-sev");
    sev.appendChild(el("span", "isx-sev__dot"));
    sev.appendChild(el("span", null, `${analysis.severity || "medium"} severity`));
    head.appendChild(sev);
    card.appendChild(head);

    const chips = el("div", "isx-chips");
    (analysis.techniques || []).forEach((t) =>
      chips.appendChild(el("span", "isx-chip", TECH_LABELS[t] || t))
    );
    card.appendChild(chips);

    card.appendChild(el("p", "isx-expl", analysis.explanation || ""));

    if (analysis.emotional_triggers && analysis.emotional_triggers.length) {
      const leans = el("div", "isx-leans");
      leans.appendChild(el("b", null, "Leans on: "));
      leans.appendChild(document.createTextNode(analysis.emotional_triggers.join(", ")));
      card.appendChild(leans);
    }

    const phrases = (analysis.highlights || []).map((h) => h.phrase);
    if (phrases.length) {
      const toggle = el("button", "isx-toggle");
      const box = el("span", "isx-toggle__box");
      toggle.appendChild(box);
      toggle.appendChild(el("span", null, "Highlight phrases in the post"));
      toggle.addEventListener("click", () => {
        highlightsOn = !highlightsOn;
        box.classList.toggle("on", highlightsOn);
        box.textContent = highlightsOn ? "✓" : "";
        highlightIn(node, phrases, highlightsOn);
      });
      card.appendChild(toggle);
    }

    const rec = el("div", "isx-rec");
    rec.appendChild(el("div", "isx-rec__t", "Before you share"));
    rec.appendChild(el("div", "isx-rec__b", analysis.recommendation || ""));
    card.appendChild(rec);
    card.appendChild(el("div", "isx-foot", "InfoShield adds context — it never hides or removes posts. You decide."));

    wrap.appendChild(card);

    bar.addEventListener("click", () => {
      expanded = !expanded;
      card.style.display = expanded ? "block" : "none";
      moreText.textContent = expanded ? "Hide" : "What's this?";
    });

    return wrap;
  }

  function injectNode(node) {
    if (node.dataset.isxInjected === "1") return; // idempotency guard
    const id = node.getAttribute("data-post-id");
    const entry = STATE.analyses.get(id);
    node.dataset.isxInjected = "1";
    if (!entry || !entry.flagged || !entry.analysis) return;

    const cs = getComputedStyle(node);
    if (cs.position === "static") node.style.position = "relative";
    node.appendChild(buildBadge());
    node.appendChild(buildAnalysis(node, entry));
    STATE.flagged.add(id);
  }

  function injectAll() {
    document.querySelectorAll("[data-post-id]").forEach(injectNode);
  }

  // ---- scan reporting (drives the page's Insights widget) ---------------
  function computeScan() {
    const scanned = document.querySelectorAll("[data-post-id]").length;
    const counter = {};
    STATE.flagged.forEach((id) => {
      const a = STATE.analyses.get(id)?.analysis;
      (a?.techniques || []).forEach((t) => (counter[t] = (counter[t] || 0) + 1));
    });
    let top = null;
    let max = 0;
    for (const [t, c] of Object.entries(counter)) {
      if (c > max) { max = c; top = t; }
    }
    return {
      scanned,
      flagged: STATE.flagged.size,
      patternsDetected: Object.keys(counter).length,
      mostCommonPattern: top ? (TECH_LABELS[top] || top) : "—",
    };
  }

  function postScan() {
    if (!STATE.active) return;
    window.postMessage({ source: "infoshield", type: "scan", payload: computeScan() }, "*");
  }

  function removeAll() {
    document.querySelectorAll("[data-post-id]").forEach((node) => {
      node.querySelectorAll(".isx-badge, .isx-wrap").forEach((n) => n.remove());
      node.querySelectorAll("mark.isx-highlight").forEach((m) => m.replaceWith(document.createTextNode(m.textContent)));
      node.normalize();
      delete node.dataset.isxInjected;
    });
    STATE.flagged.clear();
  }

  // ---- lifecycle --------------------------------------------------------
  async function start() {
    let config;
    try {
      config = await fetchJSON("/activation-target");
    } catch (e) {
      dlog("activation-target fetch failed", e);
      return; // backend down -> stay silent
    }
    STATE.target = config.target_url || "";
    dlog("target", STATE.target, "page", location.href, "match", normalize(STATE.target) === normalize(location.href));
    if (!STATE.target || normalize(STATE.target) !== normalize(location.href)) return;
    if (config.enabled === false) return;
    if (!(await getEnabled())) {
      STATE.active = true; // on the right page, but user toggled off
      return;
    }

    try {
      const feed = await fetchJSON("/feed");
      (feed.posts || []).forEach((p) =>
        STATE.analyses.set(p.id, {
          classification: p.classification,
          analysis: p.analysis,
          flagged: p.flagged,
        })
      );
      dlog("feed loaded, posts:", STATE.analyses.size);
    } catch (e) {
      dlog("feed fetch failed", e);
      return;
    }

    STATE.active = true;
    dlog("nodes at start:", document.querySelectorAll("[data-post-id]").length);
    injectAll();
    postScan();

    STATE.observer = new MutationObserver((muts) => {
      let added = false;
      for (const m of muts) {
        for (const n of m.addedNodes) {
          if (n.nodeType !== 1) continue;
          if (n.matches?.("[data-post-id]")) { injectNode(n); added = true; }
          if (n.querySelectorAll) {
            n.querySelectorAll("[data-post-id]").forEach((el) => { injectNode(el); added = true; });
          }
        }
      }
      if (added) postScan();
    });
    STATE.observer.observe(document.body, { childList: true, subtree: true });
  }

  // React to the popup toggle without a page reload.
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local" || !("enabled" in changes)) return;
    if (changes.enabled.newValue === false) {
      removeAll();
    } else if (STATE.active) {
      if (STATE.analyses.size === 0) start();
      else injectAll();
    }
  });

  // The page (React) can ask us to (re)send the latest scan -- covers the race
  // where the extension finishes before the page's listener is mounted.
  window.addEventListener("message", (e) => {
    const m = e.data;
    if (m && m.source === "infoshield-page" && m.type === "request-scan") postScan();
  });

  // Answer popup status queries.
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg?.type === "isx-status") {
      sendResponse({
        onTargetPage: STATE.active,
        flaggedCount: STATE.flagged.size,
        target: STATE.target,
        url: location.href,
      });
    }
    return true;
  });

  start();
})();
