// CONTRU ESTOQUE - Price Management Module
const PricesModule = {
  priceHistoryChart: null,

  async load() {
    await this.loadPricesTable();
    await this.loadRecentPriceChanges();
  },

  async loadPricesTable() {
    try {
      const res = await API.get('/api/products?status=active');
      const items = res.data || [];
      const tbody = document.getElementById('prices-table-tbody');
      if (!tbody) return;

      tbody.innerHTML = items.map(p => `
        <tr class="border-b border-slate-100 hover:bg-orange-50/20 text-xs">
          <td class="py-3 px-3 font-mono font-bold text-orange-600">${p.code}</td>
          <td class="py-3 px-3">
            <div class="font-semibold text-slate-900">${p.name}</div>
            <span class="text-[11px] text-slate-500">${p.category_name}</span>
          </td>
          <td class="py-3 px-3 text-slate-700">R$ ${p.cost_price.toFixed(2)}</td>
          <td class="py-3 px-3 font-bold text-slate-900">
            R$ ${p.sale_price.toFixed(2)}
            ${p.has_recent_price_change ? '<span class="ml-1 text-[9px] bg-orange-100 text-orange-700 px-1 py-0.5 rounded font-bold">Reajustado</span>' : ''}
          </td>
          <td class="py-3 px-3">
            <span class="px-2 py-0.5 rounded font-bold text-[11px] ${p.margin_percent >= 30 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
              +${p.margin_percent}%
            </span>
          </td>
          <td class="py-3 px-3 text-right space-x-1">
            <button onclick="PricesModule.openHistoryModal(${p.id})" class="px-2 py-1 text-slate-600 hover:text-orange-600 bg-slate-100 hover:bg-orange-50 rounded font-medium transition">
              Evolução
            </button>
            <button onclick="PricesModule.openUpdateModal(${p.id})" class="px-2.5 py-1 bg-orange-500 hover:bg-orange-600 text-white rounded font-medium shadow-sm transition">
              Reajustar
            </button>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      App.showToast('Erro ao carregar tabela de preços', 'error');
    }
  },

  async loadRecentPriceChanges() {
    try {
      const res = await API.get('/api/prices/recent');
      const list = res.data || [];
      const tbody = document.getElementById('prices-recent-history-tbody');
      if (!tbody) return;

      if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="py-4 text-center text-xs text-slate-400">Nenhum reajuste registrado recentemente.</td></tr>';
        return;
      }

      tbody.innerHTML = list.map(h => `
        <tr class="border-b border-slate-100 text-xs">
          <td class="py-2.5 px-3 text-slate-500">${h.created_at ? new Date(h.created_at).toLocaleDateString('pt-BR') : '-'}</td>
          <td class="py-2.5 px-3 font-semibold text-slate-800">${h.product_name}</td>
          <td class="py-2.5 px-3 text-slate-600">R$ ${h.previous_cost_price.toFixed(2)} &rarr; <b>R$ ${h.new_cost_price.toFixed(2)}</b></td>
          <td class="py-2.5 px-3 font-bold text-slate-900">R$ ${h.previous_sale_price.toFixed(2)} &rarr; <b>R$ ${h.new_sale_price.toFixed(2)}</b></td>
          <td class="py-2.5 px-3 text-slate-600 italic">"${h.reason}"</td>
          <td class="py-2.5 px-3 text-slate-500">${h.user_name || 'Sistema'}</td>
        </tr>
      `).join('');
    } catch (err) {
      console.warn('Erro ao carregar reajustes recentes:', err);
    }
  },

  async openUpdateModal(productId) {
    try {
      const res = await API.get(`/api/products/${productId}`);
      const p = res.data;
      document.getElementById('price-product-id').value = p.id;
      document.getElementById('price-product-name').textContent = `${p.code} - ${p.name}`;
      document.getElementById('price-current-cost').textContent = `R$ ${p.cost_price.toFixed(2)}`;
      document.getElementById('price-current-sale').textContent = `R$ ${p.sale_price.toFixed(2)}`;
      document.getElementById('price-new-cost').value = p.cost_price;
      document.getElementById('price-new-sale').value = p.sale_price;
      document.getElementById('price-reason').value = '';

      App.openModal('modal-price-update');
    } catch (err) {
      App.showToast('Erro ao carregar produto para reajuste', 'error');
    }
  },

  async submitPriceUpdate(e) {
    e.preventDefault();
    const reason = document.getElementById('price-reason').value.trim();
    if (!reason) {
      App.showToast('Regra 3: O motivo do reajuste de preço é estritamente obrigatório!', 'warning');
      return;
    }

    const body = {
      product_id: parseInt(document.getElementById('price-product-id').value),
      cost_price: parseFloat(document.getElementById('price-new-cost').value),
      sale_price: parseFloat(document.getElementById('price-new-sale').value),
      reason: reason,
      user_id: App.state.activeUser.id,
      user_name: App.state.activeUser.name
    };

    try {
      await API.post('/api/prices/update', body);
      App.showToast('Preço reajustado com histórico gravado!', 'success');
      App.closeModal('modal-price-update');
      this.load();
    } catch (err) {
      App.showToast(err.message || 'Erro ao reajustar preço', 'error');
    }
  },

  async openHistoryModal(productId) {
    try {
      const [prodRes, histRes] = await Promise.all([
        API.get(`/api/products/${productId}`),
        API.get(`/api/prices/history/${productId}`)
      ]);
      const p = prodRes.data;
      const history = histRes.data || [];

      document.getElementById('history-modal-product-title').textContent = `Evolução de Preço: ${p.code} - ${p.name}`;

      const tbody = document.getElementById('price-history-table-tbody');
      if (tbody) {
        if (history.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="py-4 text-center text-xs text-slate-400">Nenhum reajuste gravado para este material. Preço original de cadastro mantido.</td></tr>';
        } else {
          tbody.innerHTML = history.map(h => `
            <tr class="border-b border-slate-100 text-xs">
              <td class="py-2.5 px-3 text-slate-500">${h.created_at ? new Date(h.created_at).toLocaleString('pt-BR') : '-'}</td>
              <td class="py-2.5 px-3">R$ ${h.previous_cost_price.toFixed(2)} &rarr; <b>R$ ${h.new_cost_price.toFixed(2)}</b></td>
              <td class="py-2.5 px-3 font-bold">R$ ${h.previous_sale_price.toFixed(2)} &rarr; <b>R$ ${h.new_sale_price.toFixed(2)}</b></td>
              <td class="py-2.5 px-3 text-slate-600 italic">${h.reason}</td>
              <td class="py-2.5 px-3 text-slate-500">${h.user_name || 'Sistema'}</td>
            </tr>
          `).join('');
        }
      }

      // Renderiza gráfico de linha de evolução de preços
      const ctx = document.getElementById('chart-price-evolution');
      if (ctx && window.Chart) {
        if (this.priceHistoryChart) this.priceHistoryChart.destroy();

        const sortedHist = [...history].reverse();
        const labels = sortedHist.map(h => new Date(h.created_at).toLocaleDateString('pt-BR'));
        const costData = sortedHist.map(h => h.new_cost_price);
        const saleData = sortedHist.map(h => h.new_sale_price);

        // Se só tem o preço atual, adiciona ponto inicial
        if (labels.length === 0) {
          labels.push('Atual');
          costData.push(p.cost_price);
          saleData.push(p.sale_price);
        }

        this.priceHistoryChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [
              {
                label: 'Preço de Venda (R$)',
                data: saleData,
                borderColor: '#ea580c',
                backgroundColor: '#ea580c',
                tension: 0.2
              },
              {
                label: 'Preço de Custo (R$)',
                data: costData,
                borderColor: '#64748b',
                backgroundColor: '#64748b',
                borderDash: [5, 5],
                tension: 0.2
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } },
            scales: { y: { beginAtZero: false } }
          }
        });
      }

      App.openModal('modal-price-history');
    } catch (err) {
      App.showToast('Erro ao carregar histórico de preços', 'error');
    }
  }
};
