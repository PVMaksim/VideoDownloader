const state = {};
function getTab(tabId) {
  if (!state[tabId]) state[tabId] = { videos: [], seenUrls: new Set() };
  return state[tabId];
}
function urlKey(url) {
  try { const u = new URL(url); return u.hostname + u.pathname; }
  catch { return url.substring(0, 100); }
}
function getType(url) {
  if (url.includes("gceuproxy.com")) return "getcourse";
  if (url.includes("kinescope")) return "kinescope";
  if (url.includes("youtube.com") || url.includes("youtu.be")) return "youtube";
  if (url.includes("instagram.com")) return "instagram";
  if (url.includes("vk.com") || url.includes("vkvideo.ru")) return "vk";
  return "hls";
}
function getQuality(url) {
  if (url.includes("/master/")) return "master";
  const m = url.match(/\/(\d{3,4})\?/);
  return m ? m[1] + "p" : "HLS";
}
function getPageVideo(tabUrl, tabTitle) {
  if (!tabUrl) return null;
  if (/youtube.com\/watch\?.*v=|youtu.be\//.test(tabUrl)) {
    return { source: "page", type: "youtube", url: tabUrl, quality: "best", pageTitle: tabTitle };
  }
  if (/vk.com\/video(-?\d+_\d+|.*z=video)|vkvideo.ru/.test(tabUrl)) {
    return { source: "page", type: "vk", url: tabUrl, quality: "best", pageTitle: tabTitle };
  }
  if (/instagram.com\/(reel|p|stories)\//.test(tabUrl)) {
    return { source: "page", type: "instagram", url: tabUrl, quality: "best", pageTitle: tabTitle };
  }
  return null;
}
function videoHash(url) {
  const m = url.match(/\/playlist\/(?:master|media)\/([a-f0-9]{20,})\//);
  return m ? m[1] : urlKey(url);
}
function addVideo(tabId, url, pageTitle, overrides) {
  const hash = videoHash(url);
  const tab = getTab(tabId);
  const existing = tab.videos.find(v => videoHash(v.url) === hash);
  if (existing) {
    if (url.includes("/master/") && !existing.url.includes("/master/")) {
      existing.url = url;
      existing.quality = "master";
    }
    return;
  }
  tab.videos.push({
    id: Math.random().toString(36).slice(2, 9),
    url, type: getType(url), quality: getQuality(url),
    pageTitle: pageTitle || "Видео", timestamp: Date.now(),
    source: "network", ...overrides,
  });
  updateBadge(tabId, tab.videos.length);
}
chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    const { tabId, url } = details;
    if (tabId < 0) return;
    chrome.tabs.get(tabId, (tab) => {
      if (chrome.runtime.lastError) return;
      addVideo(tabId, url, tab && tab.title);
    });
  },
  { urls: [
    "*://*.gceuproxy.com/api/playlist/master/*",
    "*://*.gceuproxy.com/api/playlist/media/*",
    "*://*.kinescopecdn.net/*.m3u8",
    "*://*.kinescope.io/*.m3u8",
  ]}
);
function checkPageVideo(tabId, tabUrl, tabTitle) {
  const pageVideo = getPageVideo(tabUrl, tabTitle);
  if (!pageVideo) return;
  const tab = getTab(tabId);
  const exists = tab.videos.find(v => v.url === pageVideo.url);
  if (!exists) {
    tab.videos.push({
      id: Math.random().toString(36).slice(2, 9),
      ...pageVideo, timestamp: Date.now(),
    });
    updateBadge(tabId, tab.videos.length);
  }
}
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url && tab.url.startsWith("http")) {
    state[tabId] = { videos: [], seenUrls: new Set() };
    updateBadge(tabId, 0);
    checkPageVideo(tabId, tab.url, tab.title);
    chrome.scripting.executeScript({
      target: { tabId, allFrames: true },
      world: "MAIN",
      func: performanceScanner,
    }).catch(() => {});
  }
});
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.title && tab.url) {
    const existing = state[tabId]?.videos?.find(v => v.source === "page");
    if (existing) existing.pageTitle = changeInfo.title;
  }
});
function performanceScanner() {
  var PATTERNS = [/gceuproxy.com\/api\/playlist/, /kinescope.*\.m3u8/];
  function isVideo(url) { return PATTERNS.some(function(p) { return p.test(url); }); }
  function scan() {
    performance.getEntriesByType("resource").forEach(function(e) {
      if (isVideo(e.name)) window.dispatchEvent(new CustomEvent("vg_found", { detail: e.name }));
    });
  }
  try {
    var obs = new PerformanceObserver(function(list) {
      list.getEntries().forEach(function(e) {
        if (isVideo(e.name)) window.dispatchEvent(new CustomEvent("vg_found", { detail: e.name }));
      });
    });
    obs.observe({ entryTypes: ["resource"] });
  } catch(e) {}
  scan();
}
chrome.alarms.create("keepalive", { periodInMinutes: 0.4 });
chrome.alarms.onAlarm.addListener(() => {});
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "VIDEO_FOUND") {
    const tabId = sender.tab && sender.tab.id;
    if (tabId) addVideo(tabId, message.url, message.pageTitle);
    return;
  }
  if (message.type === "GET_VIDEOS") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (!tab) { sendResponse({ videos: [] }); return; }
      checkPageVideo(tab.id, tab.url, tab.title);
      sendResponse({ videos: state[tab.id]?.videos || [] });
    });
    return true;
  }
  if (message.type === "CLEAR_VIDEOS") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tabId = tabs[0]?.id;
      if (tabId) { state[tabId] = { videos: [], seenUrls: new Set() }; updateBadge(tabId, 0); }
      sendResponse({ ok: true });
    });
    return true;
  }
});
function updateBadge(tabId, count) {
  chrome.action.setBadgeText({ text: count > 0 ? String(count) : "", tabId });
  chrome.action.setBadgeBackgroundColor({ color: "#6366f1", tabId });
}
chrome.tabs.onRemoved.addListener((tabId) => { delete state[tabId]; });