// CONTRU ESTOQUE - Authentication & Session Management Module
const Auth = {
  currentUser: null,

  init() {
    this.setupListeners();
    this.checkSession();
  },

  checkSession() {
    const saved = localStorage.getItem('contru_user');
    if (saved) {
      try {
        this.currentUser = JSON.parse(saved);
        this.applyAuthenticatedState();
        return;
      } catch (e) {
        localStorage.removeItem('contru_user');
      }
    }
    // Não autenticado: exibe tela de login
    this.showLoginScreen();
  },

  showLoginScreen() {
    this.currentUser = null;
    document.getElementById('screen-login')?.classList.remove('hidden');
    document.getElementById('screen-workspace')?.classList.add('hidden');
  },

  applyAuthenticatedState() {
    if (!this.currentUser) return;

    document.getElementById('screen-login')?.classList.add('hidden');
    document.getElementById('screen-workspace')?.classList.remove('hidden');

    // Atualiza dados no cabeçalho
    const avatarEl = document.getElementById('header-user-avatar');
    const nameEl = document.getElementById('header-user-name');
    const roleEl = document.getElementById('header-user-role');
    const adminLink = document.getElementById('nav-link-admin');

    if (avatarEl) avatarEl.src = this.currentUser.avatar || 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&auto=format&fit=crop&q=80';
    if (nameEl) nameEl.textContent = this.currentUser.name;
    if (roleEl) roleEl.textContent = this.currentUser.role ? this.currentUser.role.display_name : 'Colaborador';

    // Exibe link do Painel Admin apenas para Administradores
    const isAdmin = this.currentUser.role && this.currentUser.role.name === 'admin';
    if (adminLink) {
      if (isAdmin) adminLink.classList.remove('hidden');
      else adminLink.classList.add('hidden');
    }

    // Sincroniza usuário ativo no App
    App.state.activeUser = {
      id: this.currentUser.id,
      name: this.currentUser.name,
      role: this.currentUser.role ? this.currentUser.role.name : 'viewer',
      display_role: this.currentUser.role ? this.currentUser.role.display_name : 'Consulta',
      avatar: this.currentUser.avatar
    };

    App.navigateTo('dashboard');
    App.updateNotificationsBadge();
  },

  async login(email, password) {
    const errorEl = document.getElementById('login-error-msg');
    if (errorEl) errorEl.classList.add('hidden');

    const btn = document.getElementById('btn-login-submit');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="inline-block animate-spin mr-2">⟳</span> Autenticando...';
    }

    try {
      const res = await API.post('/api/auth/login', { email, password });
      this.currentUser = res.user;
      localStorage.setItem('contru_user', JSON.stringify(res.user));
      App.showToast(`Bem-vindo(a), ${res.user.name}!`, 'success');
      this.applyAuthenticatedState();
    } catch (err) {
      if (errorEl) {
        errorEl.textContent = err.message || 'Falha na autenticação. Verifique os dados.';
        errorEl.classList.remove('hidden');
      }
      App.showToast(err.message || 'Erro ao autenticar', 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = 'Entrar no Sistema &rarr;';
      }
    }
  },

  async quickLogin(email, password) {
    document.getElementById('login-email').value = email;
    document.getElementById('login-password').value = password;
    await this.login(email, password);
  },

  async logout() {
    if (this.currentUser) {
      try {
        await API.post('/api/auth/logout', {
          user_id: this.currentUser.id,
          user_name: this.currentUser.name
        });
      } catch (e) {
        console.warn('Logout API erro:', e);
      }
    }
    localStorage.removeItem('contru_user');
    this.currentUser = null;
    App.showToast('Sessão encerrada com sucesso.', 'info');
    this.showLoginScreen();
  },

  openProfileModal() {
    if (!this.currentUser) return;
    document.getElementById('profile-modal-name').textContent = this.currentUser.name;
    document.getElementById('profile-modal-email').textContent = this.currentUser.email;
    document.getElementById('profile-modal-role').textContent = this.currentUser.role ? this.currentUser.role.display_name : 'Colaborador';
    document.getElementById('profile-modal-avatar').src = this.currentUser.avatar || 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&auto=format&fit=crop&q=80';
    
    const permsList = document.getElementById('profile-modal-perms');
    if (permsList) {
      const perms = this.currentUser.role?.permissions || [];
      permsList.innerHTML = perms.map(p => `
        <span class="text-[10px] bg-orange-50 text-orange-700 px-2 py-0.5 rounded border border-orange-200 font-medium">✓ ${p}</span>
      `).join('');
    }

    App.openModal('modal-user-profile');
  },

  openChangePasswordModal() {
    document.getElementById('form-change-password').reset();
    App.openModal('modal-change-password');
  },

  async submitChangePassword(e) {
    e.preventDefault();
    const curPass = document.getElementById('chg-current-pass').value;
    const newPass = document.getElementById('chg-new-pass').value;
    const confPass = document.getElementById('chg-confirm-pass').value;

    if (newPass !== confPass) {
      App.showToast('A nova senha e a confirmação não conferem.', 'warning');
      return;
    }

    try {
      await API.put('/api/auth/change-password', {
        user_id: this.currentUser.id,
        current_password: curPass,
        new_password: newPass
      });
      App.showToast('Sua senha foi alterada com sucesso!', 'success');
      App.closeModal('modal-change-password');
    } catch (err) {
      App.showToast(err.message || 'Erro ao alterar senha', 'error');
    }
  },

  setupListeners() {
    const loginForm = document.getElementById('form-login');
    if (loginForm && !loginForm.dataset.bound) {
      loginForm.dataset.bound = 'true';
      loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const pass = document.getElementById('login-password').value;
        this.login(email, pass);
      });
    }

    // Toggle dropdown do usuário no header
    const userMenuBtn = document.getElementById('btn-header-user-menu');
    const userDropdown = document.getElementById('header-user-dropdown');
    if (userMenuBtn && userDropdown) {
      userMenuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        userDropdown.classList.toggle('hidden');
      });
      document.addEventListener('click', () => {
        userDropdown.classList.add('hidden');
      });
    }
  }
};
