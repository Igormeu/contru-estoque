// CONTRU ESTOQUE - Audit Trail Module
const AuditModule = {
  logs: [],

  async load() {
    try {
      const res = await API.get('/api/audit?limit=150');
      this.logs = res.data || [];
      this.renderTable(this.logs);
    } catch (err) {
      App.showToast('Erro ao carregar registros de auditoria', 'error');
    }
  },

  renderTable(logs) {
    const tbody = document.getElementById('audit-table-tbody');
    if (!tbody) return;

    if (logs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="py-6 text-center text-xs text-slate-400">Nenhum evento registrado na trilha de auditoria.</td></tr>';
      return;
    }

    const actionColors = {
      'CADASTRO': 'bg-emerald-100 text-emerald-800',
      'EDICAO': 'bg-blue-100 text-blue-800',
      'INATIVACAO': 'bg-red-100 text-red-800',
      'EXCLUSAO': 'bg-red-100 text-red-800',
      'ENTRADA_ESTOQUE': 'bg-emerald-100 text-emerald-800',
      'SAIDA_ESTOQUE': 'bg-orange-100 text-orange-800',
      'AJUSTE_ESTOQUE': 'bg-amber-100 text-amber-800',
      'REAJUSTE_PRECO': 'bg-purple-100 text-purple-800',
      'CRIACAO_INVENTARIO': 'bg-cyan-100 text-cyan-800',
      'FINALIZACAO_INVENTARIO': 'bg-cyan-100 text-cyan-800',
      'VENDA_PDV': 'bg-indigo-100 text-indigo-800'
    };

    tbody.innerHTML = logs.map(l => {
      const dateStr = l.created_at ? new Date(l.created_at).toLocaleString('pt-BR') : '-';
      const badgeClass = actionColors[l.action] || 'bg-slate-100 text-slate-700';
      const hasDiff = l.before_data || l.after_data;

      return `
        <tr class="border-b border-slate-100 text-xs hover:bg-slate-50">
          <td class="py-2.5 px-3 text-slate-500">${dateStr}</td>
          <td class="py-2.5 px-3 font-semibold text-slate-800">${l.user_name || 'Sistema'}</td>
          <td class="py-2.5 px-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${badgeClass}">
              ${l.action}
            </span>
          </td>
          <td class="py-2.5 px-3 font-mono text-slate-500">${l.entity_type} #${l.entity_id || '-'}</td>
          <td class="py-2.5 px-3 text-slate-700">${l.description}</td>
          <td class="py-2.5 px-3 text-right">
            ${hasDiff ? `
              <button onclick="AuditModule.showDiffModal(${l.id})" class="text-orange-600 hover:text-orange-700 font-semibold text-[11px] underline">
                Ver Detalhes
              </button>
            ` : '<span class="text-slate-300">-</span>'}
          </td>
        </tr>
      `;
    }).join('');
  },

  showDiffModal(logId) {
    const log = this.logs.find(l => l.id === logId);
    if (!log) return;

    document.getElementById('audit-diff-action').textContent = `${log.action} (${log.entity_type} #${log.entity_id || ''})`;
    document.getElementById('audit-diff-desc').textContent = log.description;
    document.getElementById('audit-diff-user').textContent = `Responsável: ${log.user_name || 'Sistema'} em ${new Date(log.created_at).toLocaleString('pt-BR')}`;

    const beforeEl = document.getElementById('audit-diff-before');
    const afterEl = document.getElementById('audit-diff-after');

    if (beforeEl) beforeEl.textContent = log.before_data ? JSON.stringify(log.before_data, null, 2) : '// Sem dados anteriores';
    if (afterEl) afterEl.textContent = log.after_data ? JSON.stringify(log.after_data, null, 2) : '// Sem dados posteriores';

    App.openModal('modal-audit-diff');
  },

  filterByAction(action) {
    if (!action) {
      this.renderTable(this.logs);
    } else {
      const filtered = this.logs.filter(l => l.action.includes(action.toUpperCase()));
      this.renderTable(filtered);
    }
  }
};
