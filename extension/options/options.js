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

  // Проверка токена при загрузке (без запроса /me)
  const token = localStorage.getItem('token');
  if (token) {
    // Показываем профиль, данные подгрузятся при первом действии
    showProfile({ email: 'Пользователь' });
  } else {
    showAuth();
  }

  // Слушаем вход через компонент
  document.addEventListener('auth-login', (e) => {
    const { token, user } = e.detail;
    localStorage.setItem('token', token);
    // Используем user из события, не делаем лишний запрос
    showProfile(user);
  });

  // Слушаем регистрацию через компонент
  document.addEventListener('auth-register', (e) => {
    console.log('✅ Регистрация:', e.detail);
  });

  // Выход
  btnLogout?.addEventListener('click', () => {
    localStorage.removeItem('token');
    showAuth();
  });
});
