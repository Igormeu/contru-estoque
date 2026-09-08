// CONTRU ESTOQUE - Admin Panel Module (Gestão Corporativa)
const AdminModule = {
  currentTab: 'users',
  usersList: [],

  async load() {
    this.switchTab(this.currentTab);
  },

  switchTab(tabName) {
    this.currentTab = tabName;
    document.querySelectorAll('.admin-tab-btn').forEach(btn => {
      if (btn.getAttribute('data-tab') === tabName) {
        btn.classList.add('border-orange-600', 'text-orange-600');
        btn.classList.remove('border-transparent', 'text-slate-500');
      } else {
        btn.classList.remove('border-orange-600', 'text-orange-600');
        btn.classList.add('border-transparent', 'text-slate-500');
      }
    });

    document.querySelectorAll('.admin-tab-content').forEach(c => c.classList.add('hidden'));
    document.getElementById(`admin-tab-${tabName}`)?.classList.remove('hidden');

    if (tabName === 'users') this.loadUsers();
    else if (tabName === 'company') this.loadCompanySettings();
    else if (tabName === 'diagnostic') this.loadDiagnostic();
  },

  async loadUsers() {
    try {
      const res = await API.get('/api/admin/users');
      this.usersList = res.users || [];
      const tbody = document.getElementById('admin-users-tbody');
      if (!tbody) return;

      tbody.innerHTML = this.usersList.map(u => `
        <tr class="border-b border-slate-100 text-xs hover:bg-slate-50 transition">
          <td class="py-3 px-3">
            <div class="flex items-center space-x-3">
              <img src="${u.avatar || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&auto=format&fit=crop&q=80'}" class="w-8 h-8 rounded-full object-cover border border-slate-200">
              <div>
                <div class="font-bold text-slate-900">${u.name}</div>
                <div class="text-[11px] text-slate-400 font-mono">${u.email}</div>
              </div>
            </div>
          </td>
          <td class="py-3 px-3">
            <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-orange-100 text-orange-800">
              ${u.role ? u.role.display_name : 'Sem Perfil'}
            </span>
          </td>
          <td class="py-3 px-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${u.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}">
              ${u.is_active ? 'ATIVO' : 'BLOQUEADO'}
            </span>
          </td>
          <td class="py-3 px-3 text-slate-500 text-[11px]">
            ${u.last_login_at ? new Date(u.last_login_at).toLocaleString('pt-BR') : 'Nunca acessou'}
          </td>
          <td class="py-3 px-3 text-right">
            <div class="flex items-center justify-end space-x-1">
              <button onclick="AdminModule.openEditUserModal(${u.id})" class="px-2 py-1 text-slate-600 hover:text-blue-600 bg-slate-100 hover:bg-blue-50 rounded font-medium text-[11px] transition" title="Editar">
                Editar
              </button>
              <button onclick="AdminModule.openResetPassModal(${u.id})" class="px-2 py-1 text-slate-600 hover:text-purple-600 bg-slate-100 hover:bg-purple-50 rounded font-medium text-[11px] transition" title="Resetar Senha">
                Senha
              </button>
              <button onclick="AdminModule.toggleUserStatus(${u.id})" class="px-2 py-1 text-slate-600 hover:text-red-600 bg-slate-100 hover:bg-red-50 rounded font-medium text-[11px] transition" title="Alternar Acesso">
                ${u.is_active ? 'Bloquear' : 'Desbloquear'}
              </button>
            </div>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      App.showToast('Erro ao listar usuários', 'error');
    }
  },

  openNewUserModal() {
    document.getElementById('form-admin-new-user').reset();
    App.openModal('modal-admin-new-user');
  },

  async submitNewUser(e) {
    e.preventDefault();
    const body = {
      name: document.getElementById('adm-user-name').value.trim(),
      email: document.getElementById('adm-user-email').value.trim(),
      password: document.getElementById('adm-user-pass').value.trim(),
      role_id: parseInt(document.getElementById('adm-user-role').value),
      avatar: document.getElementById('adm-user-avatar').value.trim(),
      admin_user_id: Auth.currentUser?.id,
      admin_user_name: Auth.currentUser?.name
    };

    try {
      await API.post('/api/admin/users', body);
      App.showToast('Colaborador cadastrado com sucesso!', 'success');
      App.closeModal('modal-admin-new-user');
      this.loadUsers();
      App.loadInitialMetadata();
    } catch (err) {
      App.showToast(err.message || 'Erro ao cadastrar usuário', 'error');
    }
  },

  openEditUserModal(userId) {
    const user = this.usersList.find(u => u.id === userId);
    if (!user) return;

    document.getElementById('adm-edit-id').value = user.id;
    document.getElementById('adm-edit-name').value = user.name;
    document.getElementById('adm-edit-email').value = user.email;
    document.getElementById('adm-edit-role').value = user.role_id;
    document.getElementById('adm-edit-status').value = user.is_active ? 'true' : 'false';

    App.openModal('modal-admin-edit-user');
  },

  async submitEditUser(e) {
    e.preventDefault();
    const id = document.getElementById('adm-edit-id').value;
    const body = {
      name: document.getElementById('adm-edit-name').value.trim(),
      role_id: parseInt(document.getElementById('adm-edit-role').value),
      is_active: document.getElementById('adm-edit-status').value === 'true',
      admin_user_id: Auth.currentUser?.id,
      admin_user_name: Auth.currentUser?.name
    };

    try {
      await API.put(`/api/admin/users/${id}`, body);
      App.showToast('Colaborador atualizado com sucesso!', 'success');
      App.closeModal('modal-admin-edit-user');
      this.loadUsers();
      App.loadInitialMetadata();
    } catch (err) {
      App.showToast(err.message || 'Erro ao atualizar colaborador', 'error');
    }
  },

  openResetPassModal(userId) {
    const user = this.usersList.find(u => u.id === userId);
    if (!user) return;
    document.getElementById('adm-reset-id').value = user.id;
    document.getElementById('adm-reset-user-name').textContent = `${user.name} (${user.email})`;
    document.getElementById('adm-reset-pass').value = '';
    App.openModal('modal-admin-reset-pass');
  },

  async submitResetPassword(e) {
    e.preventDefault();
    const id = document.getElementById('adm-reset-id').value;
    const newPass = document.getElementById('adm-reset-pass').value.trim();

    try {
      await API.post(`/api/admin/users/${id}/reset-password`, {
        new_password: newPass,
        admin_user_id: Auth.currentUser?.id,
        admin_user_name: Auth.currentUser?.name
      });
      App.showToast('Senha redefinida com sucesso!', 'success');
      App.closeModal('modal-admin-reset-pass');
    } catch (err) {
      App.showToast(err.message || 'Erro ao redefinir senha', 'error');
    }
  },

  async toggleUserStatus(userId) {
    const user = this.usersList.find(u => u.id === userId);
    if (!user) return;

    if (!confirm(`Deseja realmente ${user.is_active ? 'bloquear o acesso de' : 'desbloquear o acesso de'} ${user.name}?`)) {
      return;
    }

    try {
      await API.post(`/api/admin/users/${userId}/toggle-status`, {
        admin_user_id: Auth.currentUser?.id,
        admin_user_name: Auth.currentUser?.name
      });
      App.showToast(`Acesso de ${user.name} atualizado!`, 'info');
      this.loadUsers();
    } catch (err) {
      App.showToast(err.message || 'Erro ao alterar status', 'error');
    }
  },

  // -------------------------------------------------------------------------
  // DADOS DA EMPRESA & POLÍTICAS
  // -------------------------------------------------------------------------
  async loadCompanySettings() {
    try {
      const res = await API.get('/api/admin/settings');
      const s = res.settings;

      document.getElementById('comp-name').value = s.company_name || '';
      document.getElementById('comp-trade').value = s.trade_name || '';
      document.getElementById('comp-cnpj').value = s.cnpj || '';
      document.getElementById('comp-ie').value = s.state_reg || '';
      document.getElementById('comp-email').value = s.email || '';
      document.getElementById('comp-phone').value = s.phone || '';
      document.getElementById('comp-address').value = s.address || '';
      document.getElementById('comp-negative-stock').checked = !!s.allow_negative_stock;
      document.getElementById('comp-default-margin').value = s.default_margin_percent || 45;
      document.getElementById('comp-inventory-days').value = s.inventory_interval_days || 90;
    } catch (err) {
      App.showToast('Erro ao carregar configurações da empresa', 'error');
    }
  },

  async saveCompanySettings(e) {
    e.preventDefault();
    const body = {
      company_name: document.getElementById('comp-name').value.trim(),
      trade_name: document.getElementById('comp-trade').value.trim(),
      cnpj: document.getElementById('comp-cnpj').value.trim(),
      state_reg: document.getElementById('comp-ie').value.trim(),
      email: document.getElementById('comp-email').value.trim(),
      phone: document.getElementById('comp-phone').value.trim(),
      address: document.getElementById('comp-address').value.trim(),
      allow_negative_stock: document.getElementById('comp-negative-stock').checked,
      default_margin_percent: parseFloat(document.getElementById('comp-default-margin').value || 45),
      inventory_interval_days: parseInt(document.getElementById('comp-inventory-days').value || 90),
      admin_user_id: Auth.currentUser?.id,
      admin_user_name: Auth.currentUser?.name
    };

    try {
      await API.put('/api/admin/settings', body);
      App.showToast('Dados corporativos e políticas salvas com sucesso!', 'success');
    } catch (err) {
      App.showToast(err.message || 'Erro ao salvar configurações', 'error');
    }
  },

  // -------------------------------------------------------------------------
  // DIAGNÓSTICO DO BANCO DE DADOS
  // -------------------------------------------------------------------------
  async loadDiagnostic() {
    try {
      const res = await API.get('/api/admin/db-diagnostic');
      const diag = res.diagnostic;

      document.getElementById('diag-provider').textContent = diag.provider;
      document.getElementById('diag-status').textContent = diag.connection_status;
      document.getElementById('diag-latency').textContent = `${diag.latency_ms} ms`;
      document.getElementById('diag-engine').textContent = diag.database_engine;

      const stats = diag.tables_stats || {};
      document.getElementById('diag-stat-products').textContent = stats.products;
      document.getElementById('diag-stat-users').textContent = stats.users;
      document.getElementById('diag-stat-movements').textContent = stats.movements;
      document.getElementById('diag-stat-inventories').textContent = stats.inventories;
      document.getElementById('diag-stat-audit').textContent = stats.audit_logs;
      document.getElementById('diag-stat-prices').textContent = stats.price_history;
    } catch (err) {
      App.showToast('Erro ao executar diagnóstico do banco', 'error');
    }
  }
};
