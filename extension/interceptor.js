// VideoGrab — Interceptor (MAIN world)
// Запускается ДО кода страницы, перехватывает fetch и XHR
// Общается с content.js через window events

(function () {
  const PATTERNS = [
    /gceuproxy\.com\/api\/playlist/,
    /kinescope\.io.*\.m3u8/,
    /\.m3u8(\?|$)/,
  ];

  function isVideoUrl(url) {
    try { return PATTERNS.some((p) => p.test(url)); }
    catch { return false; }
  }

  function dispatch(url) {
    window.dispatchEvent(new CustomEvent("__videograb_url__", { detail: url }));
  }

  // Перехват fetch
  const origFetch = window.fetch;
  window.fetch = function (...args) {
    const url = typeof args[0] === "string" ? args[0] : (args[0]?.url || "");
    if (isVideoUrl(url)) dispatch(url);
    return origFetch.apply(this, args);
  };

  // Перехват XHR
  const origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url, ...rest) {
    if (isVideoUrl(String(url))) dispatch(String(url));
    return origOpen.apply(this, [method, url, ...rest]);
  };
})();
