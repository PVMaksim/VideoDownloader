// VideoGrab — Content Script
// Слушает события от performance scanner и передаёт в background

window.addEventListener("__vg_found__", (e) => {
  const url = e.detail;
  if (!url) return;

  let type = "hls";
  if (url.includes("gceuproxy.com")) type = "getcourse";
  else if (url.includes("kinescope.io")) type = "kinescope";

  let quality = "HLS";
  if (url.includes("/master/")) quality = "master";
  else { const m = url.match(/\/(\d{3,4})\?/); if (m) quality = m[1] + "p"; }

  chrome.runtime.sendMessage({
    type: "VIDEO_FOUND",
    url, videoType: type, quality,
    pageTitle: document.title,
    pageUrl: location.href,
  });
});
