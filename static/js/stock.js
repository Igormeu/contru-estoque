// CONTRU ESTOQUE - Stock Module (Entradas, Saídas, Ajustes e Histórico)
const StockModule = {
  productsList: [],

  async load(subview = 'stock') {
    await this.fetchProductsDropdown();
    if (subview === 'entries') {
      this.loadMovementsTable('ENTRADA');
    } else if (subview === 'exits') {
      this.loadMovementsTable('SAIDA');
    } else {
      this.loadStockTable();
    }
  },

  async fetchProductsDropdown() {
    try {
      const res = await API.get('/api/products?status=active');
      this.productsList = res.data || [];
      const populate = (selId) => {
        const el = document.getElementById(selId);
        if (!el) return;
        el.innerHTML = '<option value="">Selecione o Material...</option>' +
          this.productsList.map(p => `
            <option value="${p.id}" data-stock="${p.stock_quantity}" data-cost="${p.cost_price}" data-unit="${p.unit_code}">
              ${p.code} - ${p.name} (Atual: ${p.stock_quantity} ${p.unit_code})
            </option>
          `).join('');
      };
      populate('entry-product-select');
      populate('exit-product-select');
      populate('adjust-product-select');
    } catch (e) {
      console.warn('Erro ao carregar produtos para select:', e);
    }
  },

  async loadStockTable() {
    try {
      const res = await API.get('/api/products?status=active');
      const items = res.data || [];
      const tbody = document.getElementById('stock-table-tbody');
      if (!tbody) return;

      tbody.innerHTML = items.map(p => `
        <tr class="border-b border-slate-100 hover:bg-orange-50/20 text-xs">
          <td class="py-3 px-3 font-mono font-bold text-orange-600">${p.code}</td>
          <td class="py-3 px-3 font-semibold text-slate-900">${p.name}</td>
          <td class="py-3 px-3 text-slate-500">${p.category_name}</td>
          <td class="py-3 px-3 text-slate-500">${p.location_name || '-'}</td>
          <td class="py-3 px-3 font-bold text-slate-900">${p.stock_quantity} ${p.unit_code}</td>
          <td class="py-3 px-3 text-slate-500">${p.min_stock} / ${p.max_stock}</td>
          <td class="py-3 px-3 font-semibold text-slate-800">R$ ${p.stock_value.toFixed(2)}</td>
          <td class="py-3 px-3 text-right">
            <div class="flex items-center justify-end space-x-1">
              <button onclick="StockModule.openEntryModalForProduct(${p.id})" class="px-2 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded font-medium text-[11px] transition">
                + Entrada
              </button>
              <button onclick="StockModule.openExitModalForProduct(${p.id})" class="px-2 py-1 bg-orange-50 text-orange-700 hover:bg-orange-100 rounded font-medium text-[11px] transition">
                - Saída
              </button>
              <button onclick="StockModule.openAdjustModalForProduct(${p.id})" class="px-2 py-1 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded font-medium text-[11px] transition">
                Ajustar
              </button>
            </div>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      App.showToast('Erro ao carregar saldos de estoque', 'error');
    }
  },

  async loadMovementsTable(typeFilter = null) {
    try {
      const url = typeFilter ? `/api/stock/movements?movement_type=${typeFilter}` : '/api/stock/movements';
      const res = await API.get(url);
      const list = res.data || [];
      const tbodyId = typeFilter === 'ENTRADA' ? 'entries-table-tbody' : (typeFilter === 'SAIDA' ? 'exits-table-tbody' : 'movements-history-tbody');
      const tbody = document.getElementById(tbodyId);
      if (!tbody) return;

      if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="py-6 text-center text-xs text-slate-400">Nenhum registro encontrado.</td></tr>';
        return;
      }

      tbody.innerHTML = list.map(m => `
        <tr class="border-b border-slate-100 hover:bg-slate-50/50 text-xs">
          <td class="py-2.5 px-3 text-slate-500">${m.created_at ? new Date(m.created_at).toLocaleString('pt-BR') : '-'}</td>
          <td class="py-2.5 px-3 font-bold text-slate-800">${m.product_code} - ${m.product_name}</td>
          <td class="py-2.5 px-3 font-bold ${m.movement_type === 'ENTRADA' ? 'text-emerald-600' : 'text-orange-600'}">
            ${m.movement_type === 'ENTRADA' ? '+' : '-'}${m.quantity} ${m.unit_code}
          </td>
          <td class="py-2.5 px-3 text-slate-500">${m.previous_balance} &rarr; <b>${m.new_balance}</b></td>
          <td class="py-2.5 px-3 text-slate-700">${m.origin_destination || '-'}</td>
          <td class="py-2.5 px-3 text-slate-500 font-mono">${m.document_ref || '-'}</td>
          <td class="py-2.5 px-3 text-slate-500">${m.user_name || 'Sistema'}</td>
          <td class="py-2.5 px-3 text-slate-400 italic">${m.reason_notes || '-'}</td>
        </tr>
      `).join('');
    } catch (err) {
      App.showToast('Erro ao carregar movimentações', 'error');
    }
  },

  openEntryModalForProduct(productId = null) {
    document.getElementById('form-stock-entry').reset();
    if (productId) {
      document.getElementById('entry-product-select').value = productId;
    }
    App.openModal('modal-stock-entry');
  },

  openExitModalForProduct(productId = null) {
    document.getElementById('form-stock-exit').reset();
    if (productId) {
      document.getElementById('exit-product-select').value = productId;
    }
    App.openModal('modal-stock-exit');
  },

  openAdjustModalForProduct(productId) {
    document.getElementById('form-stock-adjust').reset();
    const prod = this.productsList.find(p => p.id === productId);
    if (prod) {
      document.getElementById('adjust-product-id').value = prod.id;
      document.getElementById('adjust-product-code').textContent = `${prod.code} - ${prod.name}`;
      document.getElementById('adjust-current-stock').value = `${prod.stock_quantity} ${prod.unit_code}`;
      document.getElementById('adjust-new-quantity').value = prod.stock_quantity;
    }
    App.openModal('modal-stock-adjust');
  },

  async submitEntry(e) {
    e.preventDefault();
    const body = {
      product_id: parseInt(document.getElementById('entry-product-select').value),
      quantity: parseFloat(document.getElementById('entry-quantity').value),
      unit_price: parseFloat(document.getElementById('entry-unit-price').value || 0),
      origin_destination: document.getElementById('entry-supplier').value.trim(),
      document_ref: document.getElementById('entry-document').value.trim(),
      reason_notes: document.getElementById('entry-notes').value.trim(),
      user_id: App.state.activeUser.id,
      user_name: App.state.activeUser.name
    };

    if (!body.product_id || !body.quantity) {
      App.showToast('Selecione o material e informe a quantidade.', 'warning');
      return;
    }

    try {
      await API.post('/api/stock/entry', body);
      App.showToast('Entrada de estoque confirmada com sucesso!', 'success');
      App.closeModal('modal-stock-entry');
      App.refreshCurrentView();
      App.updateNotificationsBadge();
    } catch (err) {
      App.showToast(err.message || 'Erro ao registrar entrada', 'error');
    }
  },

  async submitExit(e) {
    e.preventDefault();
    const body = {
      product_id: parseInt(document.getElementById('exit-product-select').value),
      quantity: parseFloat(document.getElementById('exit-quantity').value),
      origin_destination: document.getElementById('exit-destination').value.trim(),
      reason_notes: document.getElementById('exit-notes').value.trim(),
      user_id: App.state.activeUser.id,
      user_name: App.state.activeUser.name
    };

    if (!body.product_id || !body.quantity) {
      App.showToast('Selecione o material e informe a quantidade.', 'warning');
      return;
    }

    try {
      await API.post('/api/stock/exit', body);
      App.showToast('Saída de estoque registrada com sucesso!', 'success');
      App.closeModal('modal-stock-exit');
      App.refreshCurrentView();
      App.updateNotificationsBadge();
    } catch (err) {
      App.showToast(err.message || 'Erro ao registrar saída', 'error');
    }
  },

  async submitAdjustment(e) {
    e.preventDefault();
    const body = {
      product_id: parseInt(document.getElementById('adjust-product-id').value),
      new_quantity: parseFloat(document.getElementById('adjust-new-quantity').value),
      justification: document.getElementById('adjust-justification').value.trim(),
      user_id: App.state.activeUser.id,
      user_name: App.state.activeUser.name
    };

    if (!body.justification) {
      App.showToast('Regra 4: A justificativa é obrigatória para qualquer ajuste de saldo!', 'warning');
      return;
    }

    try {
      await API.post('/api/stock/adjust', body);
      App.showToast('Saldo ajustado e registrado na auditoria com sucesso!', 'success');
      App.closeModal('modal-stock-adjust');
      App.refreshCurrentView();
      App.updateNotificationsBadge();
    } catch (err) {
      App.showToast(err.message || 'Erro ao ajustar estoque', 'error');
    }
  }
};
