// CONTRU ESTOQUE - Alerts & Replenishment Module
const AlertsModule = {
  async load() {
    try {
      const res = await API.get('/api/stock/replenishment');
      const items = res.data || [];
      const tbody = document.getElementById('replenishment-table-tbody');
      if (!tbody) return;

      const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
      };

      const formatBRL = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val || 0);

      const zeroCount = items.filter(i => i.stock_quantity === 0).length;
      const lowCount = items.length - zeroCount;

      setVal('replenishment-count-total', items.length);
      setVal('replenishment-count-zero', zeroCount);
      setVal('replenishment-count-low', lowCount);
      setVal('replenishment-total-cost', formatBRL(res.total_estimated_cost));

      if (items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="py-12 text-center text-xs text-slate-500 font-medium">Parabéns! Todos os materiais cadastrados estão com estoque acima do mínimo.</td></tr>';
        return;
      }

      tbody.innerHTML = items.map(it => {
        const isZero = it.stock_quantity === 0;
        return `
          <tr class="border-b border-slate-100 hover:bg-orange-50/20 text-xs">
            <td class="py-3 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${isZero ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}">
                ${isZero ? 'RUPTURA (ZERADO)' : 'ESTOQUE BAIXO'}
              </span>
            </td>
            <td class="py-3 px-3">
              <span class="font-mono font-bold text-orange-600">${it.code}</span>
              <div class="font-semibold text-slate-900">${it.name}</div>
              <span class="text-[11px] text-slate-400">${it.category_name}</span>
            </td>
            <td class="py-3 px-3 font-bold ${isZero ? 'text-red-700' : 'text-amber-700'}">
              ${it.stock_quantity} ${it.unit_code}
            </td>
            <td class="py-3 px-3 text-slate-500">${it.min_stock} ${it.unit_code}</td>
            <td class="py-3 px-3 text-slate-500">${it.max_stock} ${it.unit_code}</td>
            <td class="py-3 px-3 font-bold text-emerald-600 bg-emerald-50/50">
              +${it.suggested_restock} ${it.unit_code}
            </td>
            <td class="py-3 px-3 font-semibold text-slate-800">
              ${formatBRL(it.estimated_replenishment_cost)}
            </td>
            <td class="py-3 px-3 text-right">
              <button onclick="StockModule.openEntryModalForProduct(${it.id})" class="px-3 py-1 bg-orange-500 hover:bg-orange-600 text-white rounded font-medium shadow-sm transition">
                + Comprar / Entrada
              </button>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      App.showToast('Erro ao carregar dados de reposição', 'error');
    }
  }
};
