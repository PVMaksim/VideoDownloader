document.addEventListener('DOMContentLoaded', () => {
  const authSection = document.getElementById('authSection');
  const profileSection = document.getElementById('profileSection');
  const profileEmail = document.getElementById('profileEmail');
  const avatarLetter = document.getElementById('avatarLetter');
  const btnLogout = document.getElementById('btnLogout');

  function showProfile(user) {
    if (authSection) authSection.style.display = 'none';
    if (profileSection) profileSection.style.display = 'block';
    if (profileEmail) profileEmail.textContent = user?.email || 'Пользователь';
    if (avatarLetter) {
      const email = user?.email || '';
      avatarLetter.textContent = email.charAt(0).toUpperCase();
    }
  }

  function showAuth() {
    if (profileSection) profileSection.style.display = 'none';
    if (authSection) authSection.style.display = 'block';
  }

  // Проверка токена при загрузке — из chrome.storage.local
  chrome.storage.local.get(['token', 'userEmail'], (result) => {
    const token = result.token;
    const email = result.userEmail || 'Пользователь';
    if (token) {
      showProfile({ email });
    } else {
      showAuth();
    }
  });

  // Слушаем вход через компонент
  document.addEventListener('auth-login', (e) => {
    const { token, user } = e.detail;
    // Сохраняем в chrome.storage.local (а не в localStorage!)
    chrome.storage.local.set({
      token: token,
      userEmail: user?.email || 'Пользователь'
    }, () => {
      console.log('✅ Token saved to chrome.storage.local');
    });
    showProfile(user);
  });

  // Слушаем регистрацию через компонент
  document.addEventListener('auth-register', (e) => {
    console.log('✅ Регистрация:', e.detail);
  });

  // Выход
  btnLogout?.addEventListener('click', () => {
    chrome.storage.local.remove(['token', 'userEmail'], () => {
      console.log('✅ Token removed');
    });
    showAuth();
  });
});