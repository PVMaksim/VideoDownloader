// Content script для обнаружения видео
chrome.runtime.onMessage.addListener((msg, _sender, sendRes) => {
  if (msg.type === "GET_VIDEOS") {
    chrome.storage.local.get(["videos"], (res) => {
      sendRes(res.videos || []);
    });
  } else if (msg.type === "CLEAR_VIDEOS") {
    chrome.storage.local.set({ videos: [] }, () => {
      sendRes("cleared");
    });
  }
});

// Функция инициализации наблюдателя
function initObserver() {
  if (!document.body) {
    console.warn('[VideoDetector] document.body is null, retrying...');
    setTimeout(initObserver, 100);
    return;
  }

  const observer = new MutationObserver(() => {
    detectVideos();
  });

  observer.observe(document.body, { childList: true, subtree: true });
  
  // Первичное обнаружение
  setTimeout(detectVideos, 1000);
}

// Запускаем наблюдатель
initObserver();

function detectVideos() {
  const url = location.href;
  
  // YouTube
  if (url.includes("youtube.com/watch") || url.includes("youtu.be/")) {
    sendVideo(url, "youtube");
  }
  // Instagram
  else if (url.includes("instagram.com/reel") || url.includes("instagram.com/p/")) {
    sendVideo(url, "instagram");
  }
  // VK
  else if (url.includes("vk.com/video") || url.includes("vk.com/videos")) {
    sendVideo(url, "vk");
  }
  // GetCourse (gceuproxy.com или getcourse.ru)
  else if (url.includes("gceuproxy.com") || url.includes("getcourse.ru")) {
    sendVideo(url, "getcourse");
  }
  // Kinescope
  else if (url.includes("kinescope.io")) {
    sendVideo(url, "kinescope");
  }
}

function sendVideo(url, platform) {
  // Извлекаем название видео
  let pageTitle = document.title;
  
  // Для GetCourse пробуем найти заголовок урока
  if (platform === "getcourse") {
    // Пробуем разные селекторы для GetCourse
    const titleSelectors = [
      '.lesson-title',
      '.course-lesson__title',
      '.gc-lesson__title',
      '[data-lesson-title]',
      '.player-title',
      'h1',
      '.lesson-name',
      '.course-lesson-title'
    ];
    
    // Ищем заголовок под плеером
    for (const selector of titleSelectors) {
      const el = document.querySelector(selector);
      if (el && el.textContent.trim().length > 3) {
        pageTitle = el.textContent.trim();
        console.log('[GetCourse] Found title from selector:', selector, '->', pageTitle);
        break;
      }
    }
    
    // Если не нашли по селекторам, ищем текст под видео плеером
    if (!pageTitle || pageTitle === document.title) {
      const videoPlayer = document.querySelector('video');
      if (videoPlayer) {
        // Ищем ближайший заголовок после плеера
        const parent = videoPlayer.closest('.video-player, .player-wrapper, .lesson-content');
        if (parent) {
          const heading = parent.nextElementSibling?.querySelector('h2, h3, h4, .lesson-title, .video-title');
          if (heading && heading.textContent.trim().length > 3) {
            pageTitle = heading.textContent.trim();
            console.log('[GetCourse] Found title from video player context:', pageTitle);
          }
        }
      }
    }
    
    // Если всё ещё не нашли, используем первый заголовок на странице
    if (!pageTitle || pageTitle === document.title) {
      const firstHeading = document.querySelector('h2, h3');
      if (firstHeading && firstHeading.textContent.trim().length > 3) {
        pageTitle = firstHeading.textContent.trim();
        console.log('[GetCourse] Using first heading:', pageTitle);
      }
    }
    
    console.log('[GetCourse] Final title:', pageTitle);
  }
  
  // Определяем качество
  let quality = "HLS";
  if (url.includes("/master/")) quality = "master";
  else { 
    const m = url.match(/\/(\d{3,4})\?/); 
    if (m) quality = m[1] + "p"; 
  }

  // Отправляем сообщение
  chrome.runtime.sendMessage({
    type: "VIDEO_FOUND",
    url, 
    videoType: platform, 
    quality,
    pageTitle: pageTitle,
    pageUrl: location.href,
  });
}

// Сохраняем видео в storage
chrome.runtime.onMessage.addListener((msg, _sender, sendRes) => {
  if (msg.type === "VIDEO_FOUND") {
    chrome.storage.local.get(["videos"], (res) => {
      const videos = res.videos || [];
      
      // Проверяем, нет ли уже такого видео
      const exists = videos.some(v => v.url === msg.url);
      if (!exists) {
        videos.push({
          id: Date.now().toString(36) + Math.random().toString(36).substr(2),
          url: msg.url,
          type: msg.videoType,
          quality: msg.quality,
          pageTitle: msg.pageTitle,
          pageUrl: msg.pageUrl,
          detectedAt: new Date().toISOString(),
        });
        
        chrome.storage.local.set({ videos }, () => {
          console.log('💾 Video saved:', msg.pageTitle);
        });
      }
    });
    sendRes("ok");
  }
});