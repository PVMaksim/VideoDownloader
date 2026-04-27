// VideoGrab — Popup v0.9

const QUALITIES = [
  { label: "360p",  height: 360,  sub: "360p" },
  { label: "480p",  height: 480,  sub: "480p" },
  { label: "720p",  height: 720,  sub: "HD"   },
  { label: "1080p", height: 1080, sub: "Full HD" },
];

const PLATFORM_LABELS = {
  getcourse: "GetCourse",
  kinescope: "Kinescope",
  youtube:   "YouTube",
  instagram: "Instagram",
  vk:        "VK",
  hls:       "HLS",
};

// Платформы где качество выбирается вручную (HLS)
const HLS_PLATFORMS = new Set(["getcourse", "kinescope", "hls"]);

// Платформы где yt-dlp парсит страницу
const PAGE_PLATFORMS = new Set(["youtube", "instagram", "vk"]);

let backendUrl = "";
let apiKey = "";

document.addEventListener("DOMContentLoaded", async () => {
  const s = await chrome.storage.local.get(["backendUrl", "apiKey"]);
  backendUrl = (s.backendUrl || "").replace(/\/$/, "");
  apiKey = s.apiKey || "";
  updateFooter();

  loadVideos();
  document.getElementById("btnRefresh").addEventListener("click", loadVideos);
  document.getElementById("btnClear").addEventListener("click", () =>
    chrome.runtime.sendMessage({ type: "CLEAR_VIDEOS" }, loadVideos));
  document.getElementById("btnSettings").addEventListener("click", () =>
    chrome.runtime.openOptionsPage());
});

function updateFooter() {
  const el = document.getElementById("footerBackend");
  if (backendUrl) {
    el.textContent = "🟢 " + new URL(backendUrl).hostname;
    el.style.color = "var(--green)";
  } else {
    el.innerHTML = `⚠️ <a onclick="chrome.runtime.openOptionsPage()">настрой бэкенд</a>`;
  }
}

function loadVideos() {
  document.getElementById("statusText").textContent = "Сканирую...";
  document.getElementById("content").innerHTML =
    `<div class="loading"><div class="spinner"></div>загрузка...</div>`;
  chrome.runtime.sendMessage({ type: "GET_VIDEOS" }, (res) => {
    const videos = res?.videos || [];
    videos.length === 0 ? renderEmpty() : renderList(videos);
  });
}

function renderEmpty() {
  document.getElementById("statusText").textContent = "видео не найдено";
  document.getElementById("content").innerHTML = `
    <div class="empty">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="3" width="20" height="14" rx="2"/>
          <path d="M8 21h8M12 17v4"/>
        </svg>
      </div>
      <h3>Видео не найдено</h3>
      <p>Открой страницу с видео — YouTube, VK, Instagram, GetCourse</p>
    </div>`;
}

function renderList(videos) {
  document.getElementById("statusText").textContent = `найдено ${videos.length} видео`;
  const list = document.createElement("div");
  list.className = "list";
  videos.forEach(v => list.appendChild(buildCard(v)));
  document.getElementById("content").innerHTML = "";
  document.getElementById("content").appendChild(list);
}

function buildCard(video) {
  const card = document.createElement("div");
  card.className = "card";
  const platform = PLATFORM_LABELS[video.type] || "Видео";
  const title = cleanTitle(video.pageTitle);
  const isHls = HLS_PLATFORMS.has(video.type);
  const isPage = PAGE_PLATFORMS.has(video.type);
  let selectedHeight = 1080;

  // Блок выбора качества — только для HLS платформ
  const qualityBlock = isHls ? `
    <div class="qlabel">Качество</div>
    <div class="qgrid">
      ${QUALITIES.map((q, i) => `
        <button class="qbtn ${q.height === selectedHeight ? "sel" : ""} ${i === QUALITIES.length-1 ? "best" : ""}"
                data-h="${q.height}">
          <span class="qr">${q.label}</span>
          <span class="qs">${q.sub}</span>
        </button>`).join("")}
    </div>` : `
    <div class="quality-auto">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:11px;height:11px">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
      Лучшее доступное качество
    </div>`;

  card.innerHTML = `
    <div class="card-tag tag-${video.type}">${platform}</div>
    <div class="card-title">${esc(title)}</div>
    ${qualityBlock}
    <div class="actions">
      <button class="btn btn-dl">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Скачать
      </button>
      <button class="btn btn-open" title="Открыть">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>
          <polyline points="15 3 21 3 21 9"/>
          <line x1="10" y1="14" x2="21" y2="3"/>
        </svg>
      </button>
    </div>
    <div class="progress-wrap" id="pw-${video.id}">
      <div class="progress-bar-bg">
        <div class="progress-bar-fill" id="pb-${video.id}"></div>
      </div>
      <div class="progress-text">
        <span id="pt-${video.id}">Подготовка...</span>
        <span id="pp-${video.id}">0%</span>
      </div>
    </div>
  `;

  // Переключение качества (только HLS)
  if (isHls) {
    card.querySelectorAll(".qbtn").forEach(btn => {
      btn.addEventListener("click", () => {
        card.querySelectorAll(".qbtn").forEach(b => b.classList.remove("sel"));
        btn.classList.add("sel");
        selectedHeight = parseInt(btn.dataset.h);
      });
    });
  }

  // Скачать
  card.querySelector(".btn-dl").addEventListener("click", () => {
    if (!backendUrl || !apiKey) { chrome.runtime.openOptionsPage(); return; }
    const height = isPage ? null : selectedHeight;
    startDownload(video, height, card);
  });

  // Открыть
  card.querySelector(".btn-open").addEventListener("click", () => {
    chrome.tabs.create({ url: video.url });
  });

  return card;
}

// ── Скачивание ────────────────────────────────────────────────────
async function startDownload(video, height, card) {
  const dlBtn = card.querySelector(".btn-dl");
  const pw = card.querySelector(`#pw-${video.id}`);
  const pb = card.querySelector(`#pb-${video.id}`);
  const pt = card.querySelector(`#pt-${video.id}`);
  const pp = card.querySelector(`#pp-${video.id}`);

  setDlState(dlBtn, "loading", "Отправка...");
  card.querySelectorAll(".qbtn").forEach(b => b.disabled = true);
  pw.classList.add("visible");

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const cookies = await chrome.cookies.getAll({ url: tab.url });
    const cookieStr = cookies.map(c => `${c.name}=${c.value}`).join("; ");

    const body = {
      video_url: video.url,
      cookies: cookieStr,
      referer: tab.url,
      user_agent: navigator.userAgent,
      title: cleanTitle(video.pageTitle),
    };
    if (height) body.height = height;

    const res = await fetch(`${backendUrl}/api/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
      body: JSON.stringify(body),
    });

    if (!res.ok) throw new Error(`Сервер вернул ${res.status}`);
    const { task_id } = await res.json();

    setDlState(dlBtn, "loading", "Скачивается...");
    pt.textContent = "Скачивается на сервере...";

    await pollStatus(task_id, pb, pt, pp);

    chrome.downloads.download({
      url: `${backendUrl}/api/file/${task_id}`,
      headers: [{ name: "X-API-Key", value: apiKey }],
      saveAs: true,
    });

    setDlState(dlBtn, "done", "✓ Готово!");
    pb.classList.add("done");
    pt.textContent = "Файл скачан";

    setTimeout(() => {
      setDlState(dlBtn, "", "Скачать");
      card.querySelectorAll(".qbtn").forEach(b => b.disabled = false);
    }, 3000);

  } catch (err) {
    setDlState(dlBtn, "error", "Ошибка");
    pb.classList.add("error");
    pt.textContent = err.message;
    pp.textContent = "";
    card.querySelectorAll(".qbtn").forEach(b => b.disabled = false);
    setTimeout(() => {
      setDlState(dlBtn, "", "Скачать");
      pw.classList.remove("visible");
      pb.classList.remove("error");
    }, 4000);
  }
}

async function pollStatus(taskId, pb, pt, pp) {
  return new Promise((resolve, reject) => {
    const iv = setInterval(async () => {
      try {
        const res = await fetch(`${backendUrl}/api/status/${taskId}`, {
          headers: { "X-API-Key": apiKey },
        });
        const data = await res.json();
        const pct = Math.round(data.progress || 0);
        pb.style.width = pct + "%";
        pp.textContent = pct + "%";
        if (data.status === "ready") { clearInterval(iv); pb.style.width = "100%"; resolve(); }
        else if (data.status === "error") { clearInterval(iv); reject(new Error(data.error || "Ошибка сервера")); }
      } catch(e) { clearInterval(iv); reject(e); }
    }, 1500);
  });
}

function setDlState(btn, cls, text) {
  btn.className = "btn btn-dl" + (cls ? " " + cls : "");
  btn.disabled = cls === "loading";
  const spinner = cls === "loading"
    ? `<div style="width:12px;height:12px;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite;flex-shrink:0"></div>`
    : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:13px;height:13px;flex-shrink:0"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`;
  btn.innerHTML = spinner + " " + text;
}

function cleanTitle(t) {
  if (!t) return "video";
  return t.replace(/\s*[|–—-]\s*[^|–—-]+$/, "").trim() || t;
}

function esc(s) {
  return String(s).replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
