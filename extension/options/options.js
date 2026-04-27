document.addEventListener("DOMContentLoaded", async () => {
  const s = await chrome.storage.local.get(["backendUrl", "apiKey"]);
  if (s.backendUrl) document.getElementById("backendUrl").value = s.backendUrl;
  if (s.apiKey) document.getElementById("apiKey").value = s.apiKey;

  document.getElementById("btnSave").addEventListener("click", save);
  document.getElementById("btnTest").addEventListener("click", test);
});

async function save() {
  const url = document.getElementById("backendUrl").value.trim().replace(/\/$/, "");
  const key = document.getElementById("apiKey").value.trim();
  await chrome.storage.local.set({ backendUrl: url, apiKey: key });
  showStatus("ok", "✓ Настройки сохранены");
}

async function test() {
  const url = document.getElementById("backendUrl").value.trim().replace(/\/$/, "");
  const key = document.getElementById("apiKey").value.trim();
  showStatus("", "Проверяю...");
  try {
    const res = await fetch(`${url}/api/health`, {
      headers: { "X-API-Key": key }
    });
    if (res.ok) {
      const data = await res.json();
      showStatus("ok", `✓ Сервер работает (v${data.version})`);
    } else {
      showStatus("err", `Ошибка ${res.status}: ${res.statusText}`);
    }
  } catch (e) {
    showStatus("err", `Не могу подключиться: ${e.message}`);
  }
}

function showStatus(type, msg) {
  const el = document.getElementById("status");
  el.className = "status " + type;
  el.textContent = msg;
  if (!type) el.style.display = "none";
  else el.style.display = "block";
}
