// CONTRU ESTOQUE - Reports Module
const ReportsModule = {
  currentReportType: 'stock_position',

  async load() {
    this.setupListeners();
    await this.generateReport();
  },

  setupListeners() {
    const typeSelect = document.getElementById('report-type-select');
    if (typeSelect && !typeSelect.dataset.bound) {
      typeSelect.dataset.bound = 'true';
      typeSelect.addEventListener('change', (e) => {
        this.currentReportType = e.target.value;
        this.generateReport();
      });
    }

    const catSelect = document.getElementById('report-category-filter');
    if (catSelect && !catSelect.dataset.bound) {
      catSelect.dataset.bound = 'true';
      catSelect.addEventListener('change', () => this.generateReport());
    }
  },

  async generateReport() {
    const tbody = document.getElementById('report-results-tbody');
    const thead = document.getElementById('report-results-thead');
    if (!tbody || !thead) return;

    try {
      const type = this.currentReportType;
      const cat = document.getElementById('report-category-filter')?.value || '';

      if (type === 'stock_position' || type === 'low_stock' || type === 'zero_stock') {
        const params = new URLSearchParams();
        if (cat) params.append('category_id', cat);
        if (type === 'low_stock') params.append('stock_status', 'ESTOQUE_BAIXO');
        if (type === 'zero_stock') params.append('stock_status', 'SEM_ESTOQUE');

        const res = await API.get(`/api/products?${params.toString()}`);
        const items = res.data || [];

        thead.innerHTML = `
          <tr class="border-b border-slate-200 bg-slate-50 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
            <th class="py-2 px-3 text-left">Código</th>
            <th class="py-2 px-3 text-left">Material</th>
            <th class="py-2 px-3 text-left">Categoria</th>
            <th class="py-2 px-3 text-right">Saldo Atual</th>
            <th class="py-2 px-3 text-right">Mínimo</th>
            <th class="py-2 px-3 text-right">Custo Unitário</th>
            <th class="py-2 px-3 text-right">Preço Venda</th>
            <th class="py-2 px-3 text-right">Valor em Estoque</th>
          </tr>
        `;

        let totalValue = 0;
        let totalUnits = 0;

        tbody.innerHTML = items.map(p => {
          totalValue += p.stock_value;
          totalUnits += p.stock_quantity;
          return `
            <tr class="border-b border-slate-100 text-xs hover:bg-slate-50">
              <td class="py-2 px-3 font-mono font-bold text-orange-600">${p.code}</td>
              <td class="py-2 px-3 font-semibold text-slate-800">${p.name}</td>
              <td class="py-2 px-3 text-slate-500">${p.category_name}</td>
              <td class="py-2 px-3 text-right font-bold text-slate-900">${p.stock_quantity} ${p.unit_code}</td>
              <td class="py-2 px-3 text-right text-slate-500">${p.min_stock}</td>
              <td class="py-2 px-3 text-right text-slate-600">R$ ${p.cost_price.toFixed(2)}</td>
              <td class="py-2 px-3 text-right font-semibold text-slate-800">R$ ${p.sale_price.toFixed(2)}</td>
              <td class="py-2 px-3 text-right font-bold text-slate-900">R$ ${p.stock_value.toFixed(2)}</td>
            </tr>
          `;
        }).join('');

        document.getElementById('report-total-summary').innerHTML = `
          <div class="flex justify-between items-center bg-orange-50/50 p-3 rounded-lg border border-orange-200 text-xs">
            <span class="font-medium text-slate-700">Total de Materiais: <b>${items.length}</b> | Quantidade Total: <b>${totalUnits.toLocaleString('pt-BR')} un</b></span>
            <span class="font-bold text-orange-700 text-sm">Valor Total em Estoque: R$ ${totalValue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
          </div>
        `;

      } else if (type === 'movements') {
        const res = await API.get('/api/stock/movements?limit=300');
        const list = res.data || [];

        thead.innerHTML = `
          <tr class="border-b border-slate-200 bg-slate-50 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
            <th class="py-2 px-3 text-left">Data/Hora</th>
            <th class="py-2 px-3 text-left">Material</th>
            <th class="py-2 px-3 text-left">Tipo</th>
            <th class="py-2 px-3 text-right">Quantidade</th>
            <th class="py-2 px-3 text-left">Origem / Destino</th>
            <th class="py-2 px-3 text-left">Documento</th>
            <th class="py-2 px-3 text-left">Usuário</th>
          </tr>
        `;

        tbody.innerHTML = list.map(m => `
          <tr class="border-b border-slate-100 text-xs hover:bg-slate-50">
            <td class="py-2 px-3 text-slate-500">${m.created_at ? new Date(m.created_at).toLocaleString('pt-BR') : '-'}</td>
            <td class="py-2 px-3 font-semibold text-slate-800">${m.product_code} - ${m.product_name}</td>
            <td class="py-2 px-3 font-bold ${m.movement_type === 'ENTRADA' ? 'text-emerald-600' : 'text-orange-600'}">${m.movement_type}</td>
            <td class="py-2 px-3 text-right font-bold">${m.quantity} ${m.unit_code}</td>
            <td class="py-2 px-3 text-slate-600">${m.origin_destination || '-'}</td>
            <td class="py-2 px-3 text-slate-500 font-mono">${m.document_ref || '-'}</td>
            <td class="py-2 px-3 text-slate-500">${m.user_name || 'Sistema'}</td>
          </tr>
        `).join('');

        document.getElementById('report-total-summary').innerHTML = `
          <div class="bg-slate-50 p-2.5 rounded text-xs text-slate-600 font-medium">
            Exibindo as últimas <b>${list.length}</b> movimentações registradas.
          </div>
        `;
      }
    } catch (err) {
      App.showToast('Erro ao gerar relatório', 'error');
    }
  },

  printReport() {
    window.print();
  },

  exportCSV() {
    const type = this.currentReportType === 'movements' ? 'movements' : 'stock';
    window.location.href = `/api/reports/export/csv?type=${type}`;
  }
};
