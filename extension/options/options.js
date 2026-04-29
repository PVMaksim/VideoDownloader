// VideoGrab — Options v2 (auth)

let backendUrl = "";
let token = "";

document.addEventListener("DOMContentLoaded", async () => {
  const s = await chrome.storage.local.get(["backendUrl", "token"]);
  backendUrl = (s.backendUrl || "").replace(/\/$/, "");
  token = s.token || "";

  if (backendUrl) document.getElementById("backendUrl").value = backendUrl;

  // Если есть токен — показываем профиль
  if (token && backendUrl) await loadProfile();
  else showAuth();

  // Сервер
  document.getElementById("btnTest").addEventListener("click", testServer);
  document.getElementById("backendUrl").addEventListener("change", async (e) => {
    backendUrl = e.target.value.trim().replace(/\/$/, "");
    await chrome.storage.local.set({ backendUrl });
  });

  // Auth
  document.getElementById("btnLogin").addEventListener("click", login);
  document.getElementById("btnRegister").addEventListener("click", register);
  document.getElementById("btnLogout").addEventListener("click", logout);
  document.getElementById("linkRegister").addEventListener("click", (e) => { e.preventDefault(); showRegister(); });
  document.getElementById("linkLogin").addEventListener("click", (e) => { e.preventDefault(); showLogin(); });

  // Enter в полях
  ["email","password","regEmail","regPassword"].forEach(id => {
    document.getElementById(id)?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        if (id.startsWith("reg")) document.getElementById("btnRegister").click();
        else document.getElementById("btnLogin").click();
      }
    });
  });
});

// ── Сервер ───────────────────────────────────────────────────────

async function testServer() {
  backendUrl = document.getElementById("backendUrl").value.trim().replace(/\/$/, "");
  await chrome.storage.local.set({ backendUrl });
  showStatus("serverStatus", "info", "Проверяю...");

  try {
    const res = await fetch(`${backendUrl}/api/health`);
    if (res.ok) {
      const d = await res.json();
      showStatus("serverStatus", "ok", `✓ Сервер работает (v${d.version})`);
    } else {
      showStatus("serverStatus", "err", `Ошибка ${res.status}`);
    }
  } catch(e) {
    showStatus("serverStatus", "err", `Не подключиться: ${e.message}`);
  }
}

// ── Auth ─────────────────────────────────────────────────────────

async function login() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  if (!email || !password) return showStatus("authStatus", "err", "Заполни все поля");
  if (!backendUrl) return showStatus("authStatus", "err", "Сначала укажи URL сервера");

  showStatus("authStatus", "info", "Вхожу...");
  try {
    const res = await fetch(`${backendUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();

    if (!res.ok) {
      const msg = data.detail?.message || data.detail || "Ошибка входа";
      return showStatus("authStatus", "err", msg);
    }

    token = data.access_token;
    await chrome.storage.local.set({ token });
    await loadProfile();

  } catch(e) {
    showStatus("authStatus", "err", e.message);
  }
}

async function register() {
  const email = document.getElementById("regEmail").value.trim();
  const password = document.getElementById("regPassword").value;
  if (!email || !password) return showStatus("regStatus", "err", "Заполни все поля");
  if (!backendUrl) return showStatus("regStatus", "err", "Сначала укажи URL сервера");

  showStatus("regStatus", "info", "Регистрирую...");
  try {
    const res = await fetch(`${backendUrl}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();

    if (!res.ok) {
      const msg = data.detail?.message || data.detail || "Ошибка регистрации";
      return showStatus("regStatus", "err", msg);
    }

    showStatus("regStatus", "ok", "✓ " + data.message);

  } catch(e) {
    showStatus("regStatus", "err", e.message);
  }
}

async function logout() {
  token = "";
  await chrome.storage.local.remove("token");
  showAuth();
}

// ── Профиль ──────────────────────────────────────────────────────

async function loadProfile() {
  try {
    const res = await fetch(`${backendUrl}/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` },
    });

    if (!res.ok) {
      // Токен невалиден
      token = "";
      await chrome.storage.local.remove("token");
      return showAuth();
    }

    const user = await res.json();
    showProfile(user);

  } catch(e) {
    showAuth();
  }
}

function showProfile(user) {
  document.getElementById("loginSection").style.display = "none";
  document.getElementById("registerSection").style.display = "none";
  document.getElementById("profileSection").classList.add("visible");

  document.getElementById("avatarLetter").textContent = user.email[0].toUpperCase();
  document.getElementById("profileEmail").textContent = user.email;

  const planEl = document.getElementById("profilePlan");
  planEl.textContent = user.plan === "pro" ? "Pro" : "Free";
  planEl.className = "user-plan " + (user.plan === "pro" ? "plan-pro" : "plan-free");

  const limit = user.plan === "pro" ? "∞" : "3";
  const used = user.downloads_today;
  const max = user.plan === "pro" ? 999 : 3;
  document.getElementById("usageText").textContent = `${used} / ${limit}`;
  const pct = Math.min(100, (used / max) * 100);
  const fill = document.getElementById("usageFill");
  fill.style.width = pct + "%";
  fill.className = "usage-fill" + (used >= max ? " full" : "");
}

function showAuth() {
  document.getElementById("profileSection").classList.remove("visible");
  showLogin();
}

function showLogin() {
  document.getElementById("loginSection").style.display = "block";
  document.getElementById("registerSection").style.display = "none";
}

function showRegister() {
  document.getElementById("loginSection").style.display = "none";
  document.getElementById("registerSection").style.display = "block";
}

// ── Утилиты ──────────────────────────────────────────────────────

function showStatus(id, type, msg) {
  const el = document.getElementById(id);
  el.className = "status " + type;
  el.textContent = msg;
}
