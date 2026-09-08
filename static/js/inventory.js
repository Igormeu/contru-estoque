// CONTRU ESTOQUE - Inventory Module (Inventário e Divergências)
const InventoryModule = {
  currentInventory: null,

  async load() {
    await this.loadInventoriesList();
  },

  async loadInventoriesList() {
    try {
      const res = await API.get('/api/inventories');
      const list = res.data || [];
      const tbody = document.getElementById('inventories-table-tbody');
      if (!tbody) return;

      if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-xs text-slate-400">Nenhum inventário realizado ainda.</td></tr>';
        return;
      }

      tbody.innerHTML = list.map(inv => {
        const isDone = inv.status === 'FINALIZADO';
        return `
          <tr class="border-b border-slate-100 hover:bg-orange-50/20 text-xs">
            <td class="py-3 px-3 font-mono font-bold text-orange-600">${inv.code}</td>
            <td class="py-3 px-3 font-semibold text-slate-900">${inv.title}</td>
            <td class="py-3 px-3 text-slate-500">${inv.type}</td>
            <td class="py-3 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${isDone ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                ${inv.status}
              </span>
            </td>
            <td class="py-3 px-3 text-slate-600">${inv.total_items} materiais</td>
            <td class="py-3 px-3 font-semibold ${inv.total_diff_value !== 0 ? 'text-orange-600' : 'text-slate-500'}">
              R$ ${inv.total_diff_value.toFixed(2)}
            </td>
            <td class="py-3 px-3 text-right">
              <button onclick="InventoryModule.openConference(${inv.id})" class="px-3 py-1 bg-orange-500 hover:bg-orange-600 text-white rounded font-medium shadow-sm transition">
                ${isDone ? 'Ver Resultado' : 'Conferência'}
              </button>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      App.showToast('Erro ao carregar inventários', 'error');
    }
  },

  openNewInventoryModal() {
    document.getElementById('form-new-inventory').reset();
    App.openModal('modal-new-inventory');
  },

  async submitNewInventory(e) {
    e.preventDefault();
    const title = document.getElementById('inv-title').value.trim();
    const type = document.getElementById('inv-type').value;
    const catId = document.getElementById('inv-category').value;
    const locId = document.getElementById('inv-location').value;
    const notes = document.getElementById('inv-notes').value.trim();

    try {
      const res = await API.post('/api/inventories', {
        title: title || 'Inventário Periódico',
        type: type,
        category_id: catId ? parseInt(catId) : null,
        location_id: locId ? parseInt(locId) : null,
        notes: notes,
        user_id: App.state.activeUser.id,
        user_name: App.state.activeUser.name
      });
      App.showToast('Inventário aberto com sucesso!', 'success');
      App.closeModal('modal-new-inventory');
      this.openConference(res.data.id);
    } catch (err) {
      App.showToast(err.message || 'Erro ao criar inventário', 'error');
    }
  },

  async openConference(inventoryId) {
    try {
      const res = await API.get(`/api/inventories/${inventoryId}`);
      this.currentInventory = res.data;
      const inv = this.currentInventory;

      document.getElementById('conf-code').textContent = inv.code;
      document.getElementById('conf-title').textContent = inv.title;
      document.getElementById('conf-status').textContent = inv.status;
      document.getElementById('conf-type').textContent = `${inv.type} (${inv.category_name || inv.location_name || 'Geral'})`;

      const isReadOnly = inv.status === 'FINALIZADO';
      const finalizeBtn = document.getElementById('btn-finalize-inventory');
      const saveCountsBtn = document.getElementById('btn-save-counts');
      if (finalizeBtn) finalizeBtn.style.display = isReadOnly ? 'none' : 'inline-block';
      if (saveCountsBtn) saveCountsBtn.style.display = isReadOnly ? 'none' : 'inline-block';

      this.renderConferenceItems(inv.items || [], isReadOnly);
      this.recalculateConferenceSummary();

      App.openModal('modal-inventory-conference');
    } catch (err) {
      App.showToast('Erro ao abrir conferência do inventário', 'error');
    }
  },

  renderConferenceItems(items, isReadOnly) {
    const tbody = document.getElementById('conf-items-tbody');
    if (!tbody) return;

    tbody.innerHTML = items.map((it, idx) => `
      <tr class="border-b border-slate-100 text-xs hover:bg-slate-50" data-item-id="${it.id}">
        <td class="py-2.5 px-3">
          <span class="font-mono font-bold text-orange-600">${it.product_code}</span>
          <div class="font-semibold text-slate-800">${it.product_name}</div>
        </td>
        <td class="py-2.5 px-3 font-semibold text-slate-700">
          ${it.system_quantity} ${it.unit_code}
        </td>
        <td class="py-2.5 px-3">
          <input type="number" step="any" min="0" 
            value="${it.counted_quantity}" 
            ${isReadOnly ? 'readonly class=\"bg-slate-100 font-bold px-2 py-1 rounded w-24 border border-slate-200\"' : 'class=\"conf-counted-input font-bold px-2 py-1 rounded w-24 border border-slate-300 focus:ring-1 focus:ring-orange-500\"'}
            oninput="InventoryModule.onCountChange(this, ${it.system_quantity}, ${it.cost_price})">
        </td>
        <td class="py-2.5 px-3 font-bold conf-diff-qty ${it.diff_quantity < 0 ? 'text-red-600' : (it.diff_quantity > 0 ? 'text-emerald-600' : 'text-slate-400')}">
          ${it.diff_quantity > 0 ? '+' : ''}${it.diff_quantity}
        </td>
        <td class="py-2.5 px-3 conf-diff-pct font-semibold text-slate-600">
          ${it.diff_percent}%
        </td>
        <td class="py-2.5 px-3 conf-diff-val font-semibold ${it.diff_value < 0 ? 'text-red-600' : (it.diff_value > 0 ? 'text-emerald-600' : 'text-slate-400')}">
          R$ ${it.diff_value.toFixed(2)}
        </td>
      </tr>
    `).join('');
  },

  onCountChange(inputEl, systemQty, costPrice) {
    const countedVal = parseFloat(inputEl.value) || 0;
    const row = inputEl.closest('tr');
    const diffQty = Math.round((countedVal - systemQty) * 100) / 100;
    const diffPct = systemQty > 0 ? Math.round((diffQty / systemQty) * 1000) / 10 : (diffQty > 0 ? 100 : 0);
    const diffVal = Math.round((diffQty * costPrice) * 100) / 100;

    const qtyEl = row.querySelector('.conf-diff-qty');
    const pctEl = row.querySelector('.conf-diff-pct');
    const valEl = row.querySelector('.conf-diff-val');

    qtyEl.textContent = `${diffQty > 0 ? '+' : ''}${diffQty}`;
    pctEl.textContent = `${diffPct}%`;
    valEl.textContent = `R$ ${diffVal.toFixed(2)}`;

    qtyEl.className = `py-2.5 px-3 font-bold conf-diff-qty ${diffQty < 0 ? 'text-red-600' : (diffQty > 0 ? 'text-emerald-600' : 'text-slate-400')}`;
    valEl.className = `py-2.5 px-3 conf-diff-val font-semibold ${diffVal < 0 ? 'text-red-600' : (diffVal > 0 ? 'text-emerald-600' : 'text-slate-400')}`;

    this.recalculateConferenceSummary();
  },

  recalculateConferenceSummary() {
    const rows = document.querySelectorAll('#conf-items-tbody tr');
    let totalDivergent = 0;
    let totalValueDiff = 0;

    rows.forEach(r => {
      const qtyText = r.querySelector('.conf-diff-qty')?.textContent || '0';
      const valText = (r.querySelector('.conf-diff-val')?.textContent || '0').replace('R$', '').trim();
      const diff = parseFloat(qtyText);
      const val = parseFloat(valText);
      if (diff !== 0) totalDivergent++;
      totalValueDiff += val;
    });

    const divEl = document.getElementById('conf-summary-divergent');
    const valEl = document.getElementById('conf-summary-val');
    if (divEl) divEl.textContent = `${totalDivergent} de ${rows.length} materiais com divergência`;
    if (valEl) valEl.textContent = `Impacto Financeiro: R$ ${totalValueDiff.toFixed(2)}`;
  },

  async saveCounts() {
    if (!this.currentInventory) return;
    const rows = document.querySelectorAll('#conf-items-tbody tr');
    const counts = [];
    rows.forEach(r => {
      counts.push({
        item_id: parseInt(r.getAttribute('data-item-id')),
        counted_quantity: parseFloat(r.querySelector('.conf-counted-input')?.value || 0)
      });
    });

    try {
      await API.post(`/api/inventories/${this.currentInventory.id}/count`, { counts });
      App.showToast('Contagens salvas com sucesso!', 'success');
    } catch (err) {
      App.showToast('Erro ao salvar contagens', 'error');
    }
  },

  async finalizeInventory() {
    if (!this.currentInventory) return;
    if (!confirm('Deseja realmente finalizar este inventário? Os saldos divergentes serão atualizados automaticamente gerando movimentações do tipo INVENTÁRIO no histórico.')) {
      return;
    }

    try {
      // Salva as contagens antes de finalizar
      await this.saveCounts();

      await API.post(`/api/inventories/${this.currentInventory.id}/finalize`, {
        user_id: App.state.activeUser.id,
        user_name: App.state.activeUser.name
      });
      App.showToast('Inventário finalizado e estoques ajustados automaticamente!', 'success');
      App.closeModal('modal-inventory-conference');
      this.loadInventoriesList();
      App.updateNotificationsBadge();
    } catch (err) {
      App.showToast(err.message || 'Erro ao finalizar inventário', 'error');
    }
  }
};
