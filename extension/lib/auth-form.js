// AuthForm Web Component - с реальным сбросом пароля
class AuthForm extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    this.shadowRoot.innerHTML = this.template;
    this.api = this.getAttribute('api-url') || 'http://localhost:8000';
    this.bindEvents();
    this.loadToken();
  }

  get template() {
    return `
      <style>
        :host { display: block; font-family: system-ui, -apple-system, sans-serif; max-width: 400px; margin: 0 auto; padding: 1.5rem; background: #0f111a; border-radius: 12px; color: #e2e8f0; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
        h2 { text-align: center; margin: 0 0 1.5rem 0; color: #fff; font-size: 1.5rem; font-weight: 600; }
        .msg { padding: 0.6rem; margin-bottom: 1rem; border-radius: 6px; display: none; font-size: 0.9rem; text-align: center; }
        .msg.show { display: block; }
        .msg.error { background: #2a1215; color: #fca5a5; border: 1px solid #7f1d1d; }
        .msg.success { background: #142814; color: #86efac; border: 1px solid #166534; }
        .tabs { display: flex; border-bottom: 1px solid #334155; margin-bottom: 1.5rem; }
        .tab { padding: 0.6rem 1.2rem; cursor: pointer; color: #94a3b8; font-weight: 500; transition: all 0.2s; border-bottom: 2px solid transparent; user-select: none; }
        .tab:hover { color: #cbd5e1; }
        .tab.active { color: #818cf8; border-bottom-color: #818cf8; font-weight: 600; }
        .form { display: none; flex-direction: column; gap: 1rem; }
        .form.active { display: flex; }
        input { padding: 0.7rem; border: 1px solid #334155; background: #1e293b; color: #f8fafc; border-radius: 8px; font-size: 1rem; transition: border-color 0.2s; }
        input:focus { outline: none; border-color: #818cf8; }
        button { padding: 0.75rem; background: #6366f1; color: white; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #4f46e5; }
        .btn-reset { background: #f59e0b; margin-top: 0.5rem; }
        .btn-reset:hover { background: #d97706; }
        .btn-container { display: flex; flex-direction: column; gap: 0.5rem; }
        .password-wrapper { position: relative; display: flex; align-items: center; }
        .password-wrapper input { padding-right: 2.5rem; width: 100%; }
        .toggle-password {
            position: absolute; right: 0.7rem; top: 50%;
            transform: translateY(-50%); background: none; border: none;
            color: #94a3b8; cursor: pointer; font-size: 1.1rem;
            padding: 0.2rem; line-height: 1;
        }
        .toggle-password:hover { color: #cbd5e1; }
        .toggle-password:active { color: #818cf8; }
      </style>
      <h2>Регистрация</h2>
      <div class="msg" id="msg"></div>
      <div class="tabs">
        <div class="tab active" data-tab="login">Вход</div>
        <div class="tab" data-tab="register">Регистрация</div>
      </div>
      <form class="form active" id="loginForm">
        <input type="email" id="loginEmail" placeholder="Email" required autocomplete="email" />
        <div class="password-wrapper">
          <input type="password" id="loginPassword" placeholder="Пароль" required autocomplete="current-password" />
          <button type="button" class="toggle-password" data-target="loginPassword">👁️</button>
        </div>
        <button type="submit">Войти</button>
      </form>
      <form class="form" id="registerForm">
        <input type="email" id="registerEmail" placeholder="Email" required autocomplete="email" />
        <div class="password-wrapper">
          <input type="password" id="registerPassword" placeholder="Пароль (мин. 6)" minlength="6" required autocomplete="new-password" />
          <button type="button" class="toggle-password" data-target="registerPassword">👁️</button>
        </div>
        <div class="btn-container">
          <button type="submit">Создать аккаунт</button>
          <button type="button" class="btn-reset hidden" id="btnResetPassword">🔐 Сбросить пароль</button>
        </div>
      </form>
    `;
  }

  loadToken() {
    chrome.storage.local.get(['token'], (result) => {
      if (result.token) {
        console.log('🔑 Token loaded from storage');
      }
    });
  }

  bindEvents() {
    const sr = this.shadowRoot;
    sr.querySelectorAll('.tab').forEach(t => t.addEventListener('click', e => this.switchTab(e.target.dataset.tab)));
    sr.getElementById('loginForm').addEventListener('submit', e => this.handleLogin(e));
    sr.getElementById('registerForm').addEventListener('submit', e => this.handleRegister(e));
    sr.getElementById('btnResetPassword')?.addEventListener('click', () => this.handleResetPassword());
    sr.querySelectorAll('.toggle-password').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = btn.getAttribute('data-target');
        const input = sr.getElementById(targetId);
        if (input) {
          const isPassword = input.type === 'password';
          input.type = isPassword ? 'text' : 'password';
          btn.textContent = isPassword ? '🙈' : '👁️';
        }
      });
    });
  }

  switchTab(tab) {
    const sr = this.shadowRoot;
    sr.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
    sr.querySelectorAll('.form').forEach(f => f.classList.toggle('active', f.id === tab + 'Form'));
    this.hideMsg();
    this.hideResetButton();
  }

  showMsg(text, type, showReset = false) {
    const m = this.shadowRoot.getElementById('msg');
    m.textContent = text;
    m.className = `msg show ${type}`;
    if (showReset) {
      const btn = this.shadowRoot.getElementById('btnResetPassword');
      if (btn) btn.classList.remove('hidden');
    }
    setTimeout(() => this.hideMsg(), 5000);
  }

  hideMsg() { 
    const m = this.shadowRoot.getElementById('msg');
    m.classList.remove('show');
  }

  hideResetButton() {
    const btn = this.shadowRoot.getElementById('btnResetPassword');
    if (btn) btn.classList.add('hidden');
  }

  async handleLogin(e) {
    e.preventDefault();
    console.log(' handleLogin started');
    console.log('🔵 handleLogin called');
    const email = this.shadowRoot.getElementById('loginEmail').value;
    const pass = this.shadowRoot.getElementById('loginPassword').value;
    console.log('📝 Got email:', email);
    
    console.log('📝 Form data:', { email: email, password: '***' });
    try {
      console.log('🌐 Sending login request to:', `${this.api}/api/auth/login`);
      console.log(' Sending request...');
      const r = await fetch(`${this.api}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: pass })
      });
      console.log('📥 Response status:', r.status, r.ok);
      const d = await r.json();
      console.log('📦 Got response, has token:', !!d.access_token);
      console.log('📦 Response data:', { ...d, access_token: d.access_token ? '***' : 'missing' });
      if (!r.ok) throw new Error(d.detail);
      
      // 🔐 Надёжное сохранение токена с подтверждением
      await new Promise((resolve, reject) => {
        chrome.storage.local.set({ token: d.access_token }, () => {
          if (chrome.runtime.lastError) {
            console.error('❌ Storage error:', chrome.runtime.lastError);
            reject(chrome.runtime.lastError);
          } else {
            console.log('💾 Token saved');
            console.log('✅ Storage resolved');
            resolve();
          }
        });
      });
      
      // ✅ Проверяем, что токен действительно записался
      const check = await new Promise(res => 
        chrome.storage.local.get(['token'], res)
      );
      
      if (!check.token) {
        throw new Error('Токен не сохранился');
      }
      
      console.log('✅ Token verified');
      this.showMsg('✅ Успешный вход!', 'success');
      this.dispatchEvent(new CustomEvent('auth-login', { detail: { token: d.access_token, user: d } }));
      
      // 🔄 Перезагружаем после подтверждения
// //       setTimeout(() => window.location.reload(), 5000);
    } catch (err) { this.showMsg(err.message, 'error'); }
  }

  async handleRegister(e) {
    e.preventDefault();
    const email = this.shadowRoot.getElementById('registerEmail').value;
    const pass = this.shadowRoot.getElementById('registerPassword').value;
    try {
      const r = await fetch(`${this.api}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: pass })
      });
      console.log('📥 Response status:', r.status, r.ok);
      const d = await r.json();
      console.log('📦 Got response, has token:', !!d.access_token);
      console.log('📦 Response data:', { ...d, access_token: d.access_token ? '***' : 'missing' });
      if (!r.ok) {
        if (r.status === 409 || (d.detail && d.detail.includes('already registered'))) {
          this.showMsg('⚠️ Email уже зарегистрирован', 'error', true);
        } else {
          throw new Error(d.detail);
        }
        return;
      }
      this.showMsg('✅ Аккаунт создан! Теперь войдите.', 'success');
      setTimeout(() => this.switchTab('login'), 1500);
      this.dispatchEvent(new CustomEvent('auth-register', { detail: d }));
    } catch (err) { this.showMsg(err.message, 'error'); }
  }

  async handleResetPassword() {
    const email = this.shadowRoot.getElementById('registerEmail').value;
    if (!email || !email.includes('@')) {
      this.showMsg('⚠️ Введите корректный email', 'error');
      return;
    }
    
    const btn = this.shadowRoot.getElementById('btnResetPassword');
    btn.textContent = '⏳ Отправка...';
    btn.disabled = true;

    try {
      const r = await fetch(`${this.api}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      console.log('📥 Response status:', r.status, r.ok);
      const d = await r.json();
      console.log('📦 Got response, has token:', !!d.access_token);
      console.log('📦 Response data:', { ...d, access_token: d.access_token ? '***' : 'missing' });
      
      if (r.ok) {
        this.showMsg('📧 Токен сброшен! Проверьте КОНСОЛЬ БАЭНДЕНДА (docker compose logs api)', 'success');
        this.dispatchEvent(new CustomEvent('auth-password-reset', { detail: { email } }));
      } else {
        throw new Error(d.detail);
      }
    } catch (err) {
      this.showMsg('❌ ' + err.message, 'error');
    } finally {
      btn.textContent = '🔐 Сбросить пароль';
      btn.disabled = false;
    }
  }
}
customElements.define('auth-form', AuthForm);