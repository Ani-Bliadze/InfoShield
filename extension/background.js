// Minimal MV3 service worker: default the analysis toggle ON the first time.
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(["enabled"], (r) => {
    if (r.enabled === undefined) chrome.storage.local.set({ enabled: true });
  });
});
