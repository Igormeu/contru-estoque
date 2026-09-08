// CONTRU ESTOQUE - Core Application Controller & State
const App = {
  state: {
    currentView: 'dashboard',
    activeUser: { id: 1, name: 'Carlos Silva', role: 'admin', display_role: 'Administrador' },
    users: [],
    roles: [],
    categories: [],
    locations: [],
    units: [],
    notifications: [],
    chartInstances: {}
  },

  async init() {
    console.log('Iniciando CONTRU ESTOQUE...');
    await this.loadInitialMetadata();
    this.setupEventListeners();
    this.navigateTo('dashboard');
    this.updateNotificationsBadge();
    if (window.lucide) {
      lucide.createIcons();
    }
  },

  async loadInitialMetadata() {
    try {
      const [catsRes, locsRes, unitsRes, usersRes] = await Promise.all([
        API.get('/api/categories'),
        API.get('/api/locations'),
        API.get('/api/units'),
        API.get('/api/users')
      ]);
      this.state.categories = catsRes.data || [];
      this.state.locations = locsRes.data || [];
      this.state.units = unitsRes.data || [];
      this.state.users = usersRes.users || [];
      this.state.roles = usersRes.roles || [];

      // Popula selects de categorias e locais nos formulários
      this.populateSelects();
      this.renderUserSwitcher();
    } catch (err) {
      console.warn('Erro ao carregar metadados iniciais:', err);
    }
  },

  populateSelects() {
    const populate = (selector, items, placeholder = 'Selecione...') => {
      document.querySelectorAll(selector).forEach(sel => {
        sel.innerHTML = `<option value="">${placeholder}</option>` +
          items.map(it => `<option value="${it.id}">${it.name || it.code}</option>`).join('');
      });
    };
    populate('.select-category', this.state.categories, 'Todas as Categorias');
    populate('.select-location', this.state.locations, 'Todos os Locais');
    populate('.select-unit', this.state.units, 'Selecione a Unidade');
  },

  renderUserSwitcher() {
    const container = document.getElementById('user-switcher-container');
    if (!container) return;
    
    container.innerHTML = `
      <div class="flex items-center space-x-3 bg-white border border-slate-200 rounded-lg px-3 py-1.5 shadow-sm">
        <img src="${this.state.activeUser.avatar || 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&auto=format&fit=crop&q=80'}" class="w-7 h-7 rounded-full object-cover border border-orange-500">
        <div class="text-left hidden md:block">
          <div class="text-xs font-semibold text-slate-800 leading-tight">${this.state.activeUser.name}</div>
          <div class="text-[10px] text-orange-600 font-medium">${this.state.activeUser.display_role || 'Administrador'}</div>
        </div>
        <select id="user-role-select" class="text-xs border-none bg-slate-50 rounded px-1 py-1 text-slate-600 focus:ring-1 focus:ring-orange-500 cursor-pointer">
          ${this.state.users.map(u => `
            <option value="${u.id}" ${u.id === this.state.activeUser.id ? 'selected' : ''}>
              ${u.name} (${u.role ? u.role.display_name : 'Perfil'})
            </option>
          `).join('')}
        </select>
      </div>
    `;

    document.getElementById('user-role-select').addEventListener('change', (e) => {
      const selectedId = parseInt(e.target.value);
      const user = this.state.users.find(u => u.id === selectedId);
      if (user) {
        this.state.activeUser = {
          id: user.id,
          name: user.name,
          role: user.role ? user.role.name : 'viewer',
          display_role: user.role ? user.role.display_name : 'Consulta',
          avatar: user.avatar
        };
        this.showToast(`Perfil alterado para: ${user.name} (${this.state.activeUser.display_role})`, 'info');
        this.renderUserSwitcher();
        this.refreshCurrentView();
      }
    });
  },

  navigateTo(viewName) {
    this.state.currentView = viewName;
    console.log('Navegando para:', viewName);

    // Atualiza links da sidebar
    document.querySelectorAll('.nav-link').forEach(link => {
      const target = link.getAttribute('data-view');
      if (target === viewName) {
        link.classList.add('bg-orange-500', 'text-white', 'shadow-sm');
        link.classList.remove('text-slate-600', 'hover:bg-orange-50');
      } else {
        link.classList.remove('bg-orange-500', 'text-white', 'shadow-sm');
        link.classList.add('text-slate-600', 'hover:bg-orange-50');
      }
    });

    // Oculta todas as views e exibe a selecionada
    document.querySelectorAll('.view-section').forEach(sec => sec.classList.add('hidden'));
    const targetSection = document.getElementById(`view-${viewName}`);
    if (targetSection) {
      targetSection.classList.remove('hidden');
      targetSection.classList.add('fade-in');
    }

    // Atualiza Breadcrumbs
    const breadcrumbEl = document.getElementById('current-breadcrumb');
    if (breadcrumbEl) {
      const titles = {
        'dashboard': 'Dashboard Executivo',
        'items': 'Materiais & Catálogo',
        'entries': 'Entradas de Estoque',
        'exits': 'Saídas de Estoque',
        'stock': 'Saldo & Ajustes Manuais',
        'replenishment': 'Reposição & Alertas',
        'inventory': 'Inventário & Conferência',
        'prices': 'Gestão & Histórico de Preços',
        'reports': 'Relatórios Gerenciais',
        'pdv': 'Integração PDV',
        'audit': 'Trilha de Auditoria',
        'users': 'Usuários & Permissões',
        'structures': 'Categorias & Localizações',
        'admin': 'Painel de Administração'
      };
      breadcrumbEl.textContent = titles[viewName] || viewName;
    }

    // Carrega dados da view
    this.refreshCurrentView();
    if (window.lucide) {
      setTimeout(() => lucide.createIcons(), 50);
    }
  },

  refreshCurrentView() {
    switch (this.state.currentView) {
      case 'dashboard':
        DashboardModule.load();
        break;
      case 'items':
        ItemsModule.load();
        break;
      case 'entries':
      case 'exits':
      case 'stock':
        StockModule.load(this.state.currentView);
        break;
      case 'replenishment':
        AlertsModule.load();
        break;
      case 'inventory':
        InventoryModule.load();
        break;
      case 'prices':
        PricesModule.load();
        break;
      case 'reports':
        ReportsModule.load();
        break;
      case 'pdv':
        PDVModule.load();
        break;
      case 'audit':
        AuditModule.load();
        break;
      case 'users':
        UsersModule.load();
        break;
      case 'admin':
        AdminModule.load();
        break;
      case 'structures':
        StructuresModule.load();
        break;
    }
  },

  async updateNotificationsBadge() {
    try {
      const res = await API.get('/api/stock/replenishment');
      const count = res.total_items_needing_restock || 0;
      const badge = document.getElementById('notif-badge');
      if (badge) {
        if (count > 0) {
          badge.textContent = count;
          badge.classList.remove('hidden');
        } else {
          badge.classList.add('hidden');
        }
      }
      this.state.notifications = res.data || [];
    } catch (e) {
      console.warn('Erro ao buscar notificações:', e);
    }
  },

  showNotificationsPopover() {
    const list = document.getElementById('notif-list');
    if (!list) return;
    if (this.state.notifications.length === 0) {
      list.innerHTML = '<div class="p-4 text-center text-xs text-slate-500">Nenhum alerta pendente. Todos os estoques estão regulares!</div>';
    } else {
      list.innerHTML = this.state.notifications.slice(0, 6).map(it => `
        <div class="p-3 border-b border-slate-100 hover:bg-orange-50/50 cursor-pointer transition" onclick="App.navigateTo('replenishment'); App.toggleNotifMenu(false);">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-800">${it.code} - ${it.name}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded font-bold ${it.stock_quantity === 0 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}">
              ${it.stock_quantity === 0 ? 'RUPTURA' : 'BAIXO'}
            </span>
          </div>
          <div class="text-[11px] text-slate-500 mt-1">
            Saldo Atual: <b class="text-slate-700">${it.stock_quantity} ${it.unit_code}</b> | Mínimo: ${it.min_stock} | Repor: <span class="text-orange-600 font-semibold">+${it.suggested_restock}</span>
          </div>
        </div>
      `).join('');
    }
  },

  toggleNotifMenu(force) {
    const menu = document.getElementById('notif-menu');
    if (!menu) return;
    if (force !== undefined) {
      if (force) menu.classList.remove('hidden');
      else menu.classList.add('hidden');
    } else {
      menu.classList.toggle('hidden');
      if (!menu.classList.contains('hidden')) {
        this.showNotificationsPopover();
      }
    }
  },

  showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const bgColors = {
      success: 'bg-emerald-600 text-white',
      error: 'bg-red-600 text-white',
      warning: 'bg-amber-500 text-white',
      info: 'bg-slate-800 text-white'
    };

    toast.className = `flex items-center space-x-2 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all duration-300 transform translate-y-2 ${bgColors[type] || bgColors.success}`;
    toast.innerHTML = `<span>${message}</span>`;

    container.appendChild(toast);
    setTimeout(() => toast.classList.remove('translate-y-2'), 10);
    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-y-2');
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  openModal(id) {
    const el = document.getElementById(id);
    if (el) {
      el.classList.remove('hidden');
      el.classList.add('flex');
    }
  },

  closeModal(id) {
    const el = document.getElementById(id);
    if (el) {
      el.classList.add('hidden');
      el.classList.remove('flex');
    }
  },

  setupEventListeners() {
    // Links de navegação
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const view = link.getAttribute('data-view');
        if (view) this.navigateTo(view);
      });
    });

    // Toggle menu mobile
    const toggleBtn = document.getElementById('mobile-menu-toggle');
    const sidebar = document.getElementById('main-sidebar');
    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('-translate-x-full');
      });
    }

    // Botão de Notificações
    const notifBtn = document.getElementById('notif-button');
    if (notifBtn) {
      notifBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggleNotifMenu();
      });
    }

    document.addEventListener('click', () => {
      this.toggleNotifMenu(false);
    });
  }
};
