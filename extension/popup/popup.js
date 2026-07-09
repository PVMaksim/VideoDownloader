let selectedHeight = 1080;
// VideoGrab — Popup v1.0 (JWT auth)

const QUALITIES = [
  { label: "360p",  height: 360,  sub: "360p" },
  { label: "480p",  height: 480,  sub: "480p" },
  { label: "720p",  height: 720,  sub: "HD"   },
  { label: "1080p", height: 1080, sub: "Full HD" },
];

const PLATFORM_LABELS = {
  getcourse: "GetCourse", kinescope: "Kinescope",
  youtube: "YouTube", instagram: "Instagram", vk: "VK", hls: "HLS",
};

const HLS_PLATFORMS = new Set(["getcourse", "kinescope", "hls", "youtube", "instagram", "vk"]);
const PAGE_PLATFORMS = new Set(["youtube", "instagram", "vk"]);

const backendUrl = "https://videodownloader.neoxis.store:8450";
let token = "";

document.addEventListener("DOMContentLoaded", async () => {
  const s = await chrome.storage.local.get(["token"]);
  token = s.token || "";
  updateFooter();
  loadVideos();
  document.getElementById("btnRefresh").addEventListener("click", loadVideos);
  document.getElementById("btnClear").addEventListener("click", () =>
    chrome.runtime.sendMessage({ type: "CLEAR_VIDEOS" }, loadVideos));
  document.getElementById("btnSettings").addEventListener("click", () =>
    chrome.runtime.openOptionsPage());
});

function updateFooter() {
  const el = document.getElementById("footerStatus");
  if (!backendUrl) {
    el.innerHTML = `⚠️ <a onclick="chrome.runtime.openOptionsPage()">настрой сервер</a>`;
    el.style.color = "var(--muted)";
  } else if (!token) {
    el.innerHTML = `🔑 <a onclick="chrome.runtime.openOptionsPage()">войди в аккаунт</a>`;
    el.style.color = "#f59e0b";
  } else {
    chrome.storage.local.get(["userEmail"], (result) => {
      const email = result.userEmail || "user@example.com";
      el.textContent = "👤 " + email;
      el.style.color = "var(--green)";
    });
  }
}

function loadVideos() {
  document.getElementById("statusText").textContent = "Сканирую...";
  document.getElementById("content").innerHTML = `<div class="loading"><div class="spinner"></div>загрузка...</div>`;
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
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:11px;height:11px;flex-shrink:0">
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

  if (isHls) {
    card.querySelectorAll(".qbtn").forEach(btn => {
      btn.addEventListener("click", () => {
        card.querySelectorAll(".qbtn").forEach(b => b.classList.remove("sel"));
        btn.classList.add("sel");
        selectedHeight = parseInt(btn.dataset.h);
      });
    });
  }

  card.querySelector(".btn-dl").addEventListener("click", () => {
    startDownload(video, PAGE_PLATFORMS.has(video.type) ? null : selectedHeight, card);
  });

  return card;
}

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
      title: video.pageTitle,
      cookies: cookieStr,
      referer: tab.url,
      user_agent: navigator.userAgent,
      height: selectedHeight ? parseInt(selectedHeight, 10) : 1080,
      format: "best",
    };

    console.log("[DEBUG] Sending download request:", {
      url: video.url,
      originalTitle: video.pageTitle,
      cleanedTitle: cleanTitle(video.pageTitle),
      type: video.type,
      height: selectedHeight
    });

    if (!token) { alert("Сначала войди в аккаунт"); chrome.runtime.openOptionsPage(); return; }

    const res = await fetch(`${backendUrl}/api/downloads`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    if (res.status === 402) {
      const data = await res.json();
      throw new Error(data.detail?.message || "Лимит исчерпан");
    }
    if (res.status === 401 || res.status === 403) {
      token = "";
      await chrome.storage.local.remove("token");
      updateFooter();
      throw new Error("Сессия истекла — войди снова в настройках");
    }
    if (!res.ok) throw new Error(`Сервер вернул ${res.status}`);

    const { task_id } = await res.json();
    setDlState(dlBtn, "loading", "Скачивается...");
    pt.textContent = "Скачивается на сервере...";

    const filename = await pollStatus(task_id, pb, pt, pp);
    console.log("[DEBUG] Polling finished! Filename:", filename);

    try {
      const fileUrl = `${backendUrl}/api/downloads/file/${task_id}`;
      console.log("[DEBUG] Using Chrome Downloads API for:", fileUrl);

      chrome.downloads.download({
        url: `${fileUrl}?token=${token}`,
        filename: filename,
        saveAs: true,
        conflictAction: "uniquify"
      }, (downloadId) => {
        if (chrome.runtime.lastError) {
          console.error("[DOWNLOAD ERROR]", chrome.runtime.lastError);
          throw new Error("Ошибка при запуске скачивания");
        }
        console.log("[DOWNLOAD] Started successfully, ID:", downloadId);
      });
    } catch (err) {
      console.error("[ERROR] Download process failed:", err);
      throw new Error("Не удалось скачать файл на устройство: " + err.message);
    }

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
    }, 5000);
  }
}

async function pollStatus(taskId, pb, pt, pp) {
  return new Promise((resolve, reject) => {
    const iv = setInterval(async () => {
      try {
        const res = await fetch(`${backendUrl}/api/downloads/status/${taskId}`, {
          headers: { "Authorization": `Bearer ${token}` },
        });
        const data = await res.json();
        const pct = Math.round(data.progress || 0);
        pb.style.width = pct + "%";
        pp.textContent = pct + "%";
        if (["ready", "completed", "success"].includes(data.status)) {
          clearInterval(iv);
          pb.style.width = "100%";
          resolve(data.filename || `video_${taskId}.mp4`);
        } else if (data.status === "error") {
          clearInterval(iv);
          reject(new Error(data.error || "Ошибка сервера"));
        }
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
  let cleaned = t
    .replace(/\s*[|]\s*[^|]+$/, "")
    .replace(/\s*—\s*YouTube\s*$/i, "")
    .replace(/\s*-\s*YouTube\s*$/i, "")
    .replace(/\s*\|\s*GetCourse\s*$/i, "")
    .replace(/\s*-\s*GetCourse\s*$/i, "")
    .trim();
  return cleaned.length > 5 ? cleaned : t;
}

function esc(s) {
  return String(s).replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

document.addEventListener('click', e => {
  const btn = e.target.closest('.qbtn');
  if (btn) {
    selectedHeight = parseInt(btn.dataset.height) || 1080;
    const card = btn.closest('.card');
    if (card) {
      card.querySelectorAll('.qbtn').forEach(b => b.classList.remove('active'));
    }
    btn.classList.add('active');
    console.log("[QUALITY] Выбрано качество:", selectedHeight);
  }
});
