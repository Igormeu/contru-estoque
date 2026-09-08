// CONTRU ESTOQUE - Users, Roles & Structures Module
const UsersModule = {
  async load() {
    try {
      const res = await API.get('/api/users');
      const users = res.users || [];
      const roles = res.roles || [];

      // Renderiza Usuários
      const tbodyUsers = document.getElementById('users-table-tbody');
      if (tbodyUsers) {
        tbodyUsers.innerHTML = users.map(u => `
          <tr class="border-b border-slate-100 text-xs hover:bg-slate-50">
            <td class="py-3 px-3 flex items-center space-x-3">
              <img src="${u.avatar || 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&auto=format&fit=crop&q=80'}" class="w-8 h-8 rounded-full object-cover">
              <div>
                <div class="font-bold text-slate-900">${u.name}</div>
                <span class="text-slate-400 text-[11px]">${u.email}</span>
              </div>
            </td>
            <td class="py-3 px-3">
              <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-orange-100 text-orange-800">
                ${u.role ? u.role.display_name : 'Sem Perfil'}
              </span>
            </td>
            <td class="py-3 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${u.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}">
                ${u.is_active ? 'ATIVO' : 'INATIVO'}
              </span>
            </td>
            <td class="py-3 px-3 text-slate-500">${u.created_at ? new Date(u.created_at).toLocaleDateString('pt-BR') : '-'}</td>
          </tr>
        `).join('');
      }

      // Renderiza Matriz de Perfis
      const rolesGrid = document.getElementById('roles-cards-grid');
      if (rolesGrid) {
        rolesGrid.innerHTML = roles.map(r => `
          <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <h4 class="text-sm font-bold text-slate-800">${r.display_name}</h4>
              <span class="text-[10px] font-mono bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-bold">${r.name}</span>
            </div>
            <p class="text-xs text-slate-500 mb-3">${r.description || ''}</p>
            <div class="text-[11px] font-semibold text-slate-700 mb-1">Permissões Habilitadas:</div>
            <div class="flex flex-wrap gap-1">
              ${(r.permissions || []).map(p => `
                <span class="text-[10px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-100 font-medium">
                  ✓ ${p}
                </span>
              `).join('')}
            </div>
          </div>
        `).join('');
      }
    } catch (err) {
      App.showToast('Erro ao carregar usuários e permissões', 'error');
    }
  }
};

const StructuresModule = {
  async load() {
    try {
      const [catRes, locRes] = await Promise.all([
        API.get('/api/categories'),
        API.get('/api/locations')
      ]);

      const cats = catRes.data || [];
      const locs = locRes.data || [];

      // Categorias
      const catTbody = document.getElementById('categories-table-tbody');
      if (catTbody) {
        catTbody.innerHTML = cats.map(c => `
          <tr class="border-b border-slate-100 text-xs hover:bg-slate-50">
            <td class="py-2.5 px-3 font-semibold text-slate-800">${c.name}</td>
            <td class="py-2.5 px-3 text-slate-500">${c.description || '-'}</td>
            <td class="py-2.5 px-3 font-mono text-slate-400">${c.icon || 'tag'}</td>
          </tr>
        `).join('');
      }

      // Localizações
      const locTbody = document.getElementById('locations-table-tbody');
      if (locTbody) {
        locTbody.innerHTML = locs.map(l => `
          <tr class="border-b border-slate-100 text-xs hover:bg-slate-50">
            <td class="py-2.5 px-3 font-semibold text-slate-800">${l.name}</td>
            <td class="py-2.5 px-3 font-bold text-orange-600">${l.type}</td>
            <td class="py-2.5 px-3 text-slate-500">${l.description || '-'}</td>
          </tr>
        `).join('');
      }
    } catch (err) {
      App.showToast('Erro ao carregar estruturas físicas e categorias', 'error');
    }
  },

  async addCategory(e) {
    e.preventDefault();
    const name = document.getElementById('new-category-name').value.trim();
    const desc = document.getElementById('new-category-desc').value.trim();
    if (!name) return;

    try {
      await API.post('/api/categories', { name, description: desc });
      App.showToast('Categoria cadastrada com sucesso!', 'success');
      document.getElementById('form-new-category').reset();
      this.load();
      App.loadInitialMetadata();
    } catch (err) {
      App.showToast(err.message || 'Erro ao cadastrar categoria', 'error');
    }
  },

  async addLocation(e) {
    e.preventDefault();
    const name = document.getElementById('new-location-name').value.trim();
    const type = document.getElementById('new-location-type').value;
    const desc = document.getElementById('new-location-desc').value.trim();
    if (!name) return;

    try {
      await API.post('/api/locations', { name, type, description: desc });
      App.showToast('Localização cadastrada com sucesso!', 'success');
      document.getElementById('form-new-location').reset();
      this.load();
      App.loadInitialMetadata();
    } catch (err) {
      App.showToast(err.message || 'Erro ao cadastrar localização', 'error');
    }
  }
};
