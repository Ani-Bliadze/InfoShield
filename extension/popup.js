const BACKEND = "http://localhost:5050";

const toggle = document.getElementById("toggle");
const targetEl = document.getElementById("target");
const flaggedEl = document.getElementById("flagged");
const hintEl = document.getElementById("hint");

function setSwitch(on) {
  toggle.setAttribute("aria-checked", on ? "true" : "false");
}

function normalize(u) {
  try {
    const x = new URL(u);
    return `${x.protocol}//${x.hostname}:${x.port || ""}${x.pathname}`.replace(/\/$/, "").toLowerCase();
  } catch {
    return "";
  }
}

async function init() {
  const { enabled = true } = await chrome.storage.local.get(["enabled"]);
  setSwitch(enabled);

  // Saved target (from the landing page) via the backend.
  let target = "";
  try {
    const cfg = await (await fetch(`${BACKEND}/activation-target`, { cache: "no-store" })).json();
    target = cfg.target_url || "";
  } catch {
    targetEl.textContent = "Backend offline (:5050)";
  }
  targetEl.textContent = target || "Not set — activate from the landing page";

  // Ask the content script in the active tab for live status.
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  let status = null;
  if (tab?.id) {
    status = await chrome.tabs.sendMessage(tab.id, { type: "isx-status" }).catch(() => null);
  }

  if (!enabled) {
    flaggedEl.textContent = "Analysis is off";
    hintEl.textContent = "Turn analysis on, then refresh the target page.";
    return;
  }

  if (status?.onTargetPage) {
    flaggedEl.textContent = `${status.flaggedCount} post${status.flaggedCount === 1 ? "" : "s"} flagged on this page`;
    hintEl.textContent = "";
  } else {
    flaggedEl.textContent = "Not active on this tab";
    if (target && tab?.url && normalize(tab.url) !== normalize(target)) {
      hintEl.innerHTML = `Open the target page to see overlays.`;
    } else {
      hintEl.textContent = "Refresh the target page to activate InfoShield.";
    }
  }
}

toggle.addEventListener("click", async () => {
  const next = toggle.getAttribute("aria-checked") !== "true";
  setSwitch(next);
  await chrome.storage.local.set({ enabled: next });
  // The content script reacts to the storage change live; refresh status text.
  setTimeout(init, 150);
});

init();
