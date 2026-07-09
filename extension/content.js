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

  // Извлекаем название видео
  let pageTitle = document.title;
  
  // Для GetCourse пробуем найти заголовок урока
  if (url.includes("gceuproxy.com") || url.includes("getcourse")) {
    // Пробуем разные селекторы для GetCourse
    const titleSelectors = [
      '.lesson-title',
      '.course-lesson__title',
      'h1',
      '.gc-lesson__title',
      '[data-lesson-title]',
      '.player-title'
    ];
    
    for (const selector of titleSelectors) {
      const el = document.querySelector(selector);
      if (el && el.textContent.trim()) {
        pageTitle = el.textContent.trim();
        console.log('[GetCourse] Found title:', pageTitle, 'from selector:', selector);
        break;
      }
    }
  }

  chrome.runtime.sendMessage({
    type: "VIDEO_FOUND",
    url, videoType: type, quality,
    pageTitle: pageTitle,
    pageUrl: location.href,
  });
