// CONTRU ESTOQUE - API Client
const API = {
  async get(url) {
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok || data.success === false) {
        throw new Error(data.error || 'Erro na requisição');
      }
      return data;
    } catch (err) {
      console.error('API GET Error:', url, err);
      throw err;
    }
  },

  async post(url, body = {}) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (!res.ok || data.success === false) {
        throw new Error(data.error || 'Erro na operação');
      }
      return data;
    } catch (err) {
      console.error('API POST Error:', url, err);
      throw err;
    }
  },

  async put(url, body = {}) {
    try {
      const res = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (!res.ok || data.success === false) {
        throw new Error(data.error || 'Erro ao atualizar');
      }
      return data;
    } catch (err) {
      console.error('API PUT Error:', url, err);
      throw err;
    }
  },

  async delete(url, params = {}) {
    try {
      const query = new URLSearchParams(params).toString();
      const finalUrl = query ? `${url}?${query}` : url;
      const res = await fetch(finalUrl, { method: 'DELETE' });
      const data = await res.json();
      if (!res.ok || data.success === false) {
        throw new Error(data.error || 'Erro ao excluir');
      }
      return data;
    } catch (err) {
      console.error('API DELETE Error:', url, err);
      throw err;
    }
  }
};
