// VideoGrab — Options v2 (auth)

const backendUrl = "http://194.87.146.178:8201";
let token = "";

document.addEventListener("DOMContentLoaded", async () => {
  const s = await chrome.storage.local.get(["token"]);
  token = s.token || "";

  if (token) await loadProfile();
  else showAuth();

  // Auth buttons
  document.getElementById("btnLogin")?.addEventListener("click", () => { console.log("[DEBUG] Кнопка нажата"); login(); });
  document.getElementById("btnRegister")?.addEventListener("click", register);
  document.getElementById("btnLogout")?.addEventListener("click", logout);
  document.getElementById("linkRegister")?.addEventListener("click", (e) => { e.preventDefault(); showRegister(); });
  document.getElementById("linkLogin")?.addEventListener("click", (e) => { e.preventDefault(); showLogin(); });

  // Enter в полях
  ["email","password","regEmail","regPassword"].forEach(id => {
    document.getElementById(id)?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        if (id.startsWith("reg")) document.getElementById("btnRegister")?.click();
        else document.getElementById("btnLogin")?.click();
      }
    });
  });
});

// ── Auth ─────────────────────────────────────────────────────────

async function login() { console.log("[DEBUG] login() вызвана");
  const email = document.getElementById("email")?.value.trim();
  const password = document.getElementById("password")?.value;
  if (!email || !password) return showStatus("authStatus", "err", "Заполни все поля");

  showStatus("authStatus", "info", "Вхожу...");
  try {
    console.log("[LOGIN] Attempting...", { email: document.getElementById("loginEmail")?.value }); const res = await fetch(`${backendUrl}/api/auth/login`, {
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
  const email = document.getElementById("regEmail")?.value.trim();
  const password = document.getElementById("regPassword")?.value;
  if (!email || !password) return showStatus("regStatus", "err", "Заполни все поля");

  showStatus("regStatus", "info", "Регистрирую...");
  try {
    const res = await fetch(`${backendUrl}/api/auth/register`, {
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
    const res = await fetch(`${backendUrl}/api/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` },
    });

    if (!res.ok) {
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
  if (el) {
    el.className = "status " + type;
    el.textContent = msg;
  }
}

    // Toggle Password Visibility
    window.togglePassword = (inputEl) => {
        if(inputEl) inputEl.type = inputEl.type === 'password' ? 'text' : 'password';
    }
    
    // Add Eye Buttons to all password fields
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('input[type="password"]').forEach(el => {
            if(el.dataset.eyeAdded) return;
            el.dataset.eyeAdded = "true";
            
            const wrap = document.createElement('div');
            wrap.style.position = 'relative';
            wrap.style.width = '100%';
            el.parentNode.insertBefore(wrap, el);
            wrap.appendChild(el);
            el.style.paddingRight = '35px';
            
            const eye = document.createElement('span');
            eye.textContent = '👁';
            eye.style.cssText = 'position:absolute;right:10px;top:12px;cursor:pointer;opacity:0.7;font-size:18px;z-index:10;user-select:none;';
            eye.onclick = () => window.togglePassword(el);
            wrap.appendChild(eye);
        });
    });
    