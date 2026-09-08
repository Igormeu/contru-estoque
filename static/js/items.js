// CONTRU ESTOQUE - Items Module (Catálogo de Materiais)
const ItemsModule = {
  items: [],
  currentMode: 'table', // 'table' or 'cards'
  selectedItem: null,

  async load() {
    this.setupListeners();
    await this.fetchItems();
  },

  setupListeners() {
    const searchInput = document.getElementById('items-search-input');
    if (searchInput && !searchInput.dataset.bound) {
      searchInput.dataset.bound = 'true';
      searchInput.addEventListener('input', () => this.filterAndRender());
    }

    const catFilter = document.getElementById('items-category-filter');
    if (catFilter && !catFilter.dataset.bound) {
      catFilter.dataset.bound = 'true';
      catFilter.addEventListener('change', () => this.fetchItems());
    }

    const statusFilter = document.getElementById('items-status-filter');
    if (statusFilter && !statusFilter.dataset.bound) {
      statusFilter.dataset.bound = 'true';
      statusFilter.addEventListener('change', () => this.fetchItems());
    }

    const stockFilter = document.getElementById('items-stock-filter');
    if (stockFilter && !stockFilter.dataset.bound) {
      stockFilter.dataset.bound = 'true';
      stockFilter.addEventListener('change', () => this.fetchItems());
    }
  },

  async fetchItems() {
    try {
      const search = document.getElementById('items-search-input')?.value || '';
      const cat = document.getElementById('items-category-filter')?.value || '';
      const status = document.getElementById('items-status-filter')?.value || 'active';
      const stock = document.getElementById('items-stock-filter')?.value || '';

      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (cat) params.append('category_id', cat);
      if (status) params.append('status', status);
      if (stock) params.append('stock_status', stock);

      const res = await API.get(`/api/products?${params.toString()}`);
      this.items = res.data || [];
      this.filterAndRender();
    } catch (err) {
      console.error('Erro ao buscar materiais:', err);
      App.showToast('Erro ao carregar lista de materiais', 'error');
    }
  },

  filterAndRender() {
    const search = (document.getElementById('items-search-input')?.value || '').toLowerCase();
    const filtered = this.items.filter(it => {
      if (!search) return true;
      return (
        it.code.toLowerCase().includes(search) ||
        it.name.toLowerCase().includes(search) ||
        (it.description && it.description.toLowerCase().includes(search)) ||
        (it.category_name && it.category_name.toLowerCase().includes(search))
      );
    });

    const countEl = document.getElementById('items-total-counter');
    if (countEl) countEl.textContent = `${filtered.length} materiais encontrados`;

    if (this.currentMode === 'table') {
      this.renderTable(filtered);
    } else {
      this.renderCards(filtered);
    }
  },

  setViewMode(mode) {
    this.currentMode = mode;
    const btnTable = document.getElementById('btn-view-table');
    const btnCards = document.getElementById('btn-view-cards');
    const tblContainer = document.getElementById('items-table-container');
    const crdContainer = document.getElementById('items-cards-container');

    if (mode === 'table') {
      btnTable?.classList.add('bg-white', 'shadow-sm', 'text-orange-600');
      btnCards?.classList.remove('bg-white', 'shadow-sm', 'text-orange-600');
      tblContainer?.classList.remove('hidden');
      crdContainer?.classList.add('hidden');
    } else {
      btnCards?.classList.add('bg-white', 'shadow-sm', 'text-orange-600');
      btnTable?.classList.remove('bg-white', 'shadow-sm', 'text-orange-600');
      crdContainer?.classList.remove('hidden');
      tblContainer?.classList.add('hidden');
    }
    this.filterAndRender();
  },

  renderTable(items) {
    const tbody = document.getElementById('items-table-tbody');
    if (!tbody) return;

    if (items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="py-8 text-center text-xs text-slate-500">Nenhum material localizado com os filtros selecionados.</td></tr>';
      return;
    }

    tbody.innerHTML = items.map(p => {
      let badgeClass = 'badge-normal';
      let badgeText = 'Normal';
      if (p.stock_status === 'SEM_ESTOQUE') {
        badgeClass = 'badge-ruptura';
        badgeText = 'Sem Estoque';
      } else if (p.stock_status === 'ESTOQUE_BAIXO') {
        badgeClass = 'badge-baixo';
        badgeText = 'Estoque Baixo';
      } else if (p.stock_status === 'EXCEDENTE') {
        badgeClass = 'badge-excedente';
        badgeText = 'Excedente';
      }

      return `
        <tr class="border-b border-slate-100 hover:bg-orange-50/30 transition">
          <td class="py-3 px-4">
            <div class="flex items-center space-x-3">
              <img src="${p.image_url || 'https://images.unsplash.com/photo-1581094288338-2314dddb7ece?w=200&auto=format&fit=crop&q=80'}" class="w-10 h-10 rounded-lg object-cover border border-slate-200">
              <div>
                <span class="text-xs font-mono font-bold text-orange-600">${p.code}</span>
                <div class="text-xs font-semibold text-slate-900 line-clamp-1">${p.name}</div>
                <span class="text-[11px] text-slate-500">${p.category_name}</span>
              </div>
            </div>
          </td>
          <td class="py-3 px-3 text-xs text-slate-600">${p.unit_code}</td>
          <td class="py-3 px-3 text-xs font-bold text-slate-900">${p.stock_quantity.toLocaleString('pt-BR')}</td>
          <td class="py-3 px-3 text-xs text-slate-500">${p.min_stock} / ${p.max_stock}</td>
          <td class="py-3 px-3 text-xs">
            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${badgeClass}">
              ${badgeText}
            </span>
          </td>
          <td class="py-3 px-3 text-xs text-slate-600">R$ ${p.cost_price.toFixed(2)}</td>
          <td class="py-3 px-3 text-xs font-semibold text-slate-900">
            R$ ${p.sale_price.toFixed(2)}
            ${p.has_recent_price_change ? '<span class="ml-1 text-[9px] bg-orange-100 text-orange-700 px-1 rounded">Novo</span>' : ''}
          </td>
          <td class="py-3 px-3 text-xs text-slate-500">${p.location_name || '-'}</td>
          <td class="py-3 px-3 text-right">
            <div class="flex items-center justify-end space-x-1">
              <button onclick="ItemsModule.openDetails(${p.id})" title="Detalhes Ficha Técnica" class="p-1.5 text-slate-500 hover:text-orange-600 hover:bg-orange-50 rounded">
                <i data-lucide="eye" class="w-4 h-4"></i>
              </button>
              <button onclick="ItemsModule.openEditModal(${p.id})" title="Editar Material" class="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded">
                <i data-lucide="edit-3" class="w-4 h-4"></i>
              </button>
              <button onclick="ItemsModule.confirmDelete(${p.id})" title="Excluir / Inativar" class="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded">
                <i data-lucide="trash-2" class="w-4 h-4"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    if (window.lucide) lucide.createIcons();
  },

  renderCards(items) {
    const grid = document.getElementById('items-cards-grid');
    if (!grid) return;

    if (items.length === 0) {
      grid.innerHTML = '<div class="col-span-full py-12 text-center text-xs text-slate-500">Nenhum material localizado.</div>';
      return;
    }

    grid.innerHTML = items.map(p => {
      let badgeClass = 'badge-normal';
      let badgeText = 'Normal';
      if (p.stock_status === 'SEM_ESTOQUE') {
        badgeClass = 'badge-ruptura';
        badgeText = 'Sem Estoque';
      } else if (p.stock_status === 'ESTOQUE_BAIXO') {
        badgeClass = 'badge-baixo';
        badgeText = 'Estoque Baixo';
      }

      return `
        <div class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition flex flex-col justify-between">
          <div class="relative h-40 overflow-hidden bg-slate-100">
            <img src="${p.image_url || 'https://images.unsplash.com/photo-1581094288338-2314dddb7ece?w=400&auto=format&fit=crop&q=80'}" class="w-full h-full object-cover">
            <div class="absolute top-2 left-2 bg-white/90 backdrop-blur-sm px-2 py-0.5 rounded text-[10px] font-mono font-bold text-orange-600 shadow-sm">
              ${p.code}
            </div>
            <div class="absolute top-2 right-2">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${badgeClass}">
                ${badgeText}
              </span>
            </div>
          </div>
          <div class="p-4 flex-1 flex flex-col justify-between">
            <div>
              <div class="text-[11px] text-slate-500 mb-0.5">${p.category_name}</div>
              <h4 class="text-sm font-bold text-slate-900 leading-tight mb-2 line-clamp-2">${p.name}</h4>
            </div>
            
            <div class="bg-slate-50 rounded-lg p-2.5 my-2 text-xs space-y-1">
              <div class="flex justify-between">
                <span class="text-slate-500">Estoque:</span>
                <span class="font-bold text-slate-900">${p.stock_quantity} ${p.unit_code}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-500">Preço Venda:</span>
                <span class="font-bold text-orange-600">R$ ${p.sale_price.toFixed(2)}</span>
              </div>
            </div>

            <div class="flex items-center justify-between pt-2 border-t border-slate-100">
              <span class="text-[10px] text-slate-400 truncate">${p.location_name || 'Almoxarifado'}</span>
              <div class="flex space-x-1">
                <button onclick="ItemsModule.openDetails(${p.id})" class="px-2 py-1 text-xs bg-slate-100 hover:bg-orange-50 hover:text-orange-600 rounded font-medium transition">
                  Ver Ficha
                </button>
                <button onclick="StockModule.openEntryModalForProduct(${p.id})" class="px-2 py-1 text-xs bg-orange-500 hover:bg-orange-600 text-white rounded font-medium shadow-sm transition">
                  + Entrada
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) lucide.createIcons();
  },

  async openDetails(id) {
    try {
      const res = await API.get(`/api/products/${id}`);
      const p = res.data;
      this.selectedItem = p;

      document.getElementById('detail-code').textContent = p.code;
      document.getElementById('detail-name').textContent = p.name;
      document.getElementById('detail-desc').textContent = p.description || 'Sem descrição cadastrada.';
      document.getElementById('detail-category').textContent = p.category_name;
      document.getElementById('detail-location').textContent = p.location_name || 'Não informada';
      document.getElementById('detail-unit').textContent = p.unit_code;
      document.getElementById('detail-stock').textContent = `${p.stock_quantity} ${p.unit_code}`;
      document.getElementById('detail-min').textContent = p.min_stock;
      document.getElementById('detail-max').textContent = p.max_stock;
      document.getElementById('detail-cost').textContent = `R$ ${p.cost_price.toFixed(2)}`;
      document.getElementById('detail-sale').textContent = `R$ ${p.sale_price.toFixed(2)}`;
      document.getElementById('detail-margin').textContent = `${p.margin_percent}%`;
      document.getElementById('detail-valuation').textContent = `R$ ${p.stock_value.toFixed(2)}`;
      document.getElementById('detail-img').src = p.image_url || 'https://images.unsplash.com/photo-1581094288338-2314dddb7ece?w=400&auto=format&fit=crop&q=80';

      // Histórico de movimentações do item
      const movTbody = document.getElementById('detail-movements-tbody');
      if (movTbody) {
        if (!p.recent_movements || p.recent_movements.length === 0) {
          movTbody.innerHTML = '<tr><td colspan="5" class="py-3 text-center text-xs text-slate-400">Nenhuma movimentação registrada.</td></tr>';
        } else {
          movTbody.innerHTML = p.recent_movements.map(m => `
            <tr class="border-b border-slate-100 text-xs">
              <td class="py-2 px-2 text-slate-500">${m.created_at ? new Date(m.created_at).toLocaleDateString('pt-BR') : '-'}</td>
              <td class="py-2 px-2 font-semibold">${m.movement_type}</td>
              <td class="py-2 px-2 font-bold ${m.movement_type === 'ENTRADA' ? 'text-emerald-600' : 'text-slate-800'}">${m.movement_type === 'ENTRADA' ? '+' : '-'}${m.quantity}</td>
              <td class="py-2 px-2 text-slate-500">${m.origin_destination || '-'}</td>
              <td class="py-2 px-2 text-slate-400">${m.user_name || 'Sistema'}</td>
            </tr>
          `).join('');
        }
      }

      App.openModal('modal-item-details');
    } catch (err) {
      App.showToast('Erro ao carregar detalhes do material', 'error');
    }
  },

  openNewModal() {
    document.getElementById('form-item').reset();
    document.getElementById('item-id').value = '';
    document.getElementById('modal-item-title').textContent = 'Cadastrar Novo Material';
    document.getElementById('item-initial-stock-container').classList.remove('hidden');
    App.openModal('modal-item-form');
  },

  async openEditModal(id) {
    try {
      const res = await API.get(`/api/products/${id}`);
      const p = res.data;
      document.getElementById('item-id').value = p.id;
      document.getElementById('item-code').value = p.code;
      document.getElementById('item-code').readOnly = true;
      document.getElementById('item-name').value = p.name;
      document.getElementById('item-description').value = p.description || '';
      document.getElementById('item-category').value = p.category_id;
      document.getElementById('item-unit').value = p.unit_id;
      document.getElementById('item-location').value = p.location_id || '';
      document.getElementById('item-min-stock').value = p.min_stock;
      document.getElementById('item-max-stock').value = p.max_stock;
      document.getElementById('item-image-url').value = p.image_url || '';
      document.getElementById('item-pdv-code').value = p.pdv_code || '';
      document.getElementById('item-cost-price').value = p.cost_price;
      document.getElementById('item-sale-price').value = p.sale_price;

      // Oculta campo de estoque inicial na edição (saldo só se altera via movimentação/ajuste!)
      document.getElementById('item-initial-stock-container').classList.add('hidden');
      document.getElementById('modal-item-title').textContent = `Editar Material: ${p.code}`;

      App.openModal('modal-item-form');
    } catch (err) {
      App.showToast('Erro ao carregar dados para edição', 'error');
    }
  },

  async saveItem(e) {
    e.preventDefault();
    const id = document.getElementById('item-id').value;
    const body = {
      code: document.getElementById('item-code').value.trim(),
      name: document.getElementById('item-name').value.trim(),
      description: document.getElementById('item-description').value.trim(),
      category_id: document.getElementById('item-category').value,
      unit_id: document.getElementById('item-unit').value,
      location_id: document.getElementById('item-location').value || null,
      min_stock: parseFloat(document.getElementById('item-min-stock').value || 10),
      max_stock: parseFloat(document.getElementById('item-max-stock').value || 100),
      cost_price: parseFloat(document.getElementById('item-cost-price').value || 0),
      sale_price: parseFloat(document.getElementById('item-sale-price').value || 0),
      image_url: document.getElementById('item-image-url').value.trim(),
      pdv_code: document.getElementById('item-pdv-code').value.trim(),
      user_id: App.state.activeUser.id,
      user_name: App.state.activeUser.name
    };

    try {
      if (id) {
        await API.put(`/api/products/${id}`, body);
        App.showToast('Material atualizado com sucesso!', 'success');
      } else {
        body.initial_stock = parseFloat(document.getElementById('item-initial-stock').value || 0);
        await API.post('/api/products', body);
        App.showToast('Material cadastrado com sucesso!', 'success');
      }
      App.closeModal('modal-item-form');
      this.fetchItems();
      App.updateNotificationsBadge();
    } catch (err) {
      App.showToast(err.message || 'Erro ao salvar material', 'error');
    }
  },

  async confirmDelete(id) {
    if (!confirm('Deseja realmente excluir ou inativar este material? (Regra de integridade: materiais com histórico de movimentações serão apenas inativados).')) {
      return;
    }
    try {
      const res = await API.delete(`/api/products/${id}`, {
        user_id: App.state.activeUser.id,
        user_name: App.state.activeUser.name
      });
      App.showToast(res.result.message, 'info');
      this.fetchItems();
    } catch (err) {
      App.showToast(err.message || 'Erro ao excluir material', 'error');
    }
  }
};
