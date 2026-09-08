// CONTRU ESTOQUE - Dashboard Module
const DashboardModule = {
  charts: {},

  async load() {
    try {
      const res = await API.get('/api/dashboard');
      const data = res.data;
      this.renderKPIs(data.kpis);
      this.renderCharts(data.charts);
      this.renderAlerts(data.alerts);
      this.renderRecentMovements(data.recent_movements);
    } catch (err) {
      console.error('Erro ao carregar dashboard:', err);
      App.showToast('Erro ao carregar dados do dashboard', 'error');
    }
  },

  renderKPIs(kpis) {
    if (!kpis) return;
    const formatBRL = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val || 0);

    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    setVal('kpi-total-items', kpis.total_items);
    setVal('kpi-active-items', kpis.active_items);
    setVal('kpi-total-stock', `${kpis.total_stock_quantity.toLocaleString('pt-BR')} un`);
    setVal('kpi-stock-value', formatBRL(kpis.total_stock_value));
    setVal('kpi-low-stock', kpis.low_stock_count);
    setVal('kpi-zero-stock', kpis.zero_stock_count);
    setVal('kpi-entries-month', `+${kpis.entries_this_month.toLocaleString('pt-BR')}`);
    setVal('kpi-exits-month', `-${kpis.exits_this_month.toLocaleString('pt-BR')}`);
  },

  renderCharts(charts) {
    if (!charts || !window.Chart) return;

    // Destroi gráficos antigos para evitar sobreposição
    Object.values(this.charts).forEach(c => c && c.destroy && c.destroy());
    this.charts = {};

    // 1. Entradas x Saídas
    const ctxComp = document.getElementById('chart-entries-exits');
    if (ctxComp && charts.comparison) {
      this.charts.comparison = new Chart(ctxComp, {
        type: 'bar',
        data: {
          labels: charts.comparison.labels,
          datasets: [
            {
              label: 'Entradas (unidades)',
              data: charts.comparison.entries,
              backgroundColor: '#10b981',
              borderRadius: 4
            },
            {
              label: 'Saídas (unidades)',
              data: charts.comparison.exits,
              backgroundColor: '#ea580c',
              borderRadius: 4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom' } },
          scales: { y: { beginAtZero: true } }
        }
      });
    }

    // 2. Valor por Categoria
    const ctxCat = document.getElementById('chart-category-valuation');
    if (ctxCat && charts.category_valuation) {
      this.charts.category = new Chart(ctxCat, {
        type: 'doughnut',
        data: {
          labels: charts.category_valuation.categories,
          datasets: [{
            data: charts.category_valuation.values,
            backgroundColor: [
              '#ea580c', '#f97316', '#fb923c', '#fdba74', 
              '#3b82f6', '#10b981', '#6366f1', '#8b5cf6'
            ]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } }
          }
        }
      });
    }

    // 3. Top 5 Mais Movimentados
    const ctxTop = document.getElementById('chart-top-moved');
    if (ctxTop && charts.top_moved) {
      this.charts.top = new Chart(ctxTop, {
        type: 'bar',
        data: {
          labels: charts.top_moved.map(i => `${i.code}`),
          datasets: [{
            label: 'Volume Total Movimentado',
            data: charts.top_moved.map(i => i.quantity),
            backgroundColor: '#ea580c',
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { x: { beginAtZero: true } }
        }
      });
    }
  },

  renderAlerts(alerts) {
    const list = document.getElementById('dashboard-alerts-list');
    if (!list) return;

    if (!alerts || (!alerts.critical_stock?.length && !alerts.recent_price_changes?.length)) {
      list.innerHTML = '<div class="text-sm text-slate-500 py-3 text-center">Nenhum alerta crítico no momento. Estoques em conformidade!</div>';
      return;
    }

    let html = '';
    // Alertas de estoque
    (alerts.critical_stock || []).forEach(item => {
      const isZero = item.urgency === 'RUPTURA';
      html += `
        <div class="flex items-center justify-between p-3 rounded-lg border ${isZero ? 'bg-red-50/70 border-red-200' : 'bg-amber-50/70 border-amber-200'}">
          <div class="flex items-center space-x-3">
            <span class="w-2.5 h-2.5 rounded-full ${isZero ? 'bg-red-600' : 'bg-amber-500'}"></span>
            <div>
              <div class="text-xs font-bold text-slate-800">${item.code} - ${item.name}</div>
              <div class="text-[11px] text-slate-500">
                Saldo: <b class="${isZero ? 'text-red-700' : 'text-amber-700'}">${item.current}</b> | Mínimo estipulado: ${item.min}
              </div>
            </div>
          </div>
          <button onclick="StockModule.openEntryModalForProduct(${item.id})" class="px-2 py-1 text-xs font-semibold bg-white border border-slate-200 rounded hover:bg-orange-50 hover:text-orange-600 shadow-sm transition">
            Repor
          </button>
        </div>
      `;
    });

    // Alertas de reajustes de preços recentes
    (alerts.recent_price_changes || []).slice(0, 3).forEach(p => {
      html += `
        <div class="flex items-center justify-between p-3 rounded-lg border bg-orange-50/50 border-orange-200">
          <div class="flex items-center space-x-3">
            <span class="w-2.5 h-2.5 rounded-full bg-orange-500"></span>
            <div>
              <div class="text-xs font-bold text-slate-800">${p.product_name}</div>
              <div class="text-[11px] text-slate-500">
                Novo Preço de Venda: <b>R$ ${p.new_sale_price.toFixed(2)}</b> (era R$ ${p.previous_sale_price.toFixed(2)})
              </div>
            </div>
          </div>
          <span class="text-[10px] bg-orange-100 text-orange-800 px-2 py-0.5 rounded font-medium">Reajustado</span>
        </div>
      `;
    });

    list.innerHTML = html;
  },

  renderRecentMovements(movements) {
    const tbody = document.getElementById('dashboard-recent-movements-tbody');
    if (!tbody) return;

    if (!movements || movements.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-xs text-slate-500">Nenhuma movimentação recente registrada.</td></tr>';
      return;
    }

    const typeBadges = {
      'ENTRADA': 'bg-emerald-100 text-emerald-800 border-emerald-200',
      'SAIDA': 'bg-orange-100 text-orange-800 border-orange-200',
      'AJUSTE': 'bg-amber-100 text-amber-800 border-amber-200',
      'INVENTARIO': 'bg-blue-100 text-blue-800 border-blue-200',
      'PDV_VENDA': 'bg-purple-100 text-purple-800 border-purple-200'
    };

    tbody.innerHTML = movements.map(m => {
      const dateStr = m.created_at ? new Date(m.created_at).toLocaleString('pt-BR') : '-';
      const badgeClass = typeBadges[m.movement_type] || 'bg-slate-100 text-slate-800 border-slate-200';
      return `
        <tr class="border-b border-slate-100 hover:bg-slate-50/50 transition">
          <td class="py-2.5 px-3 text-xs text-slate-600">${dateStr}</td>
          <td class="py-2.5 px-3 text-xs font-medium text-slate-800">${m.product_code} - ${m.product_name}</td>
          <td class="py-2.5 px-3 text-xs">
            <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold border ${badgeClass}">
              ${m.movement_type}
            </span>
          </td>
          <td class="py-2.5 px-3 text-xs font-bold ${m.movement_type === 'ENTRADA' ? 'text-emerald-600' : 'text-slate-800'}">
            ${m.movement_type === 'ENTRADA' ? '+' : '-'}${m.quantity} ${m.unit_code}
          </td>
          <td class="py-2.5 px-3 text-xs text-slate-600">${m.origin_destination || '-'}</td>
          <td class="py-2.5 px-3 text-xs text-slate-500">${m.user_name || 'Sistema'}</td>
        </tr>
      `;
    }).join('');
  }
};
