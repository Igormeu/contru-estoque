// CONTRU ESTOQUE - PDV Integration Module (Preparação & Simulador)
const PDVModule = {
  async load() {
    await this.loadStatus();
    await this.populateSimulatorProducts();
  },

  async loadStatus() {
    try {
      const res = await API.get('/api/pdv/status');
      const data = res.data;

      const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
      };

      setVal('pdv-status-badge', data.status);
      setVal('pdv-system-name', data.system_name);
      setVal('pdv-last-sync', data.last_sync_at);
      setVal('pdv-configured-items', `${data.configured_pdv_items} de ${data.total_active_items} itens`);
      setVal('pdv-sales-count', data.pdv_sales_total);
      setVal('pdv-endpoint-url', data.api_endpoint);
    } catch (err) {
      App.showToast('Erro ao obter status da integração PDV', 'error');
    }
  },

  async populateSimulatorProducts() {
    try {
      const res = await API.get('/api/products?status=active');
      const products = res.data || [];
      const select = document.getElementById('pdv-sim-product-select');
      if (!select) return;

      select.innerHTML = '<option value="">Selecione o produto para a venda...</option>' +
        products.map(p => `
          <option value="${p.id}" data-price="${p.sale_price}" data-stock="${p.stock_quantity}">
            ${p.code} - ${p.name} (Preço PDV: R$ ${p.sale_price.toFixed(2)} | Estoque: ${p.stock_quantity} ${p.unit_code})
          </option>
        `).join('');

      select.addEventListener('change', (e) => {
        const opt = select.options[select.selectedIndex];
        const price = opt?.getAttribute('data-price') || 0;
        const priceInput = document.getElementById('pdv-sim-unit-price');
        if (priceInput) priceInput.value = price;
        this.recalculateSimTotal();
      });
    } catch (err) {
      console.warn('Erro ao carregar produtos para simulador:', err);
    }
  },

  recalculateSimTotal() {
    const price = parseFloat(document.getElementById('pdv-sim-unit-price')?.value || 0);
    const qty = parseFloat(document.getElementById('pdv-sim-qty')?.value || 1);
    const totalEl = document.getElementById('pdv-sim-total');
    if (totalEl) totalEl.textContent = `R$ ${(price * qty).toFixed(2)}`;
  },

  async simulateSale(e) {
    e.preventDefault();
    const productId = parseInt(document.getElementById('pdv-sim-product-select').value);
    const qty = parseFloat(document.getElementById('pdv-sim-qty').value || 1);
    const price = parseFloat(document.getElementById('pdv-sim-unit-price').value || 0);
    const terminal = document.getElementById('pdv-sim-terminal').value || 'CAIXA-01';

    if (!productId) {
      App.showToast('Selecione um produto para simular a venda.', 'warning');
      return;
    }

    try {
      const payload = {
        sale_document: `CUPOM-PDV-${Math.floor(Date.now() / 1000)}`,
        terminal_id: terminal,
        user_id: App.state.activeUser.id,
        user_name: `Operador Caixa (${App.state.activeUser.name})`,
        items: [
          {
            product_id: productId,
            quantity: qty,
            unit_price: price
          }
        ]
      };

      const res = await API.post('/api/pdv/sale', payload);
      App.showToast(`Venda ${res.document} processada! Estoque baixado automaticamente no CONTRU ESTOQUE.`, 'success');
      this.loadStatus();
      this.populateSimulatorProducts();
      App.updateNotificationsBadge();
    } catch (err) {
      App.showToast(err.message || 'Erro ao processar venda no PDV', 'error');
    }
  },

  async triggerManualSync() {
    try {
      const res = await API.post('/api/pdv/sync', {});
      App.showToast(res.message, 'success');
      this.loadStatus();
    } catch (err) {
      App.showToast('Erro ao sincronizar PDV', 'error');
    }
  }
};
