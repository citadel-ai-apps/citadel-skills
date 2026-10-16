// Client REST di PocketBase. Nessun DOM: `fetch` e `storage` arrivano da fuori,
// così i test li sostituiscono. Nel browser: creaClient({ fetch: fetch.bind(window), storage: localStorage }).

function errore(status, messaggio) {
  const e = new Error(messaggio);
  e.status = status;
  return e;
}

export function creaClient({ base = '', fetch, storage, chiave = 'sessione' }) {
  // Lo storage può mancare o lanciare (navigazione privata): la sessione vive comunque in memoria.
  let sessione = null;
  try { sessione = JSON.parse(storage.getItem(chiave)) || null; } catch { sessione = null; }

  function salva(s) {
    sessione = s;
    try { s ? storage.setItem(chiave, JSON.stringify(s)) : storage.removeItem(chiave); } catch { /* solo memoria */ }
  }

  async function chiama(path, { method = 'GET', body, auth = true } = {}) {
    const headers = {};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (auth && sessione) headers.Authorization = sessione.token;
    const opt = { method, headers };
    if (body !== undefined) opt.body = JSON.stringify(body);
    let r;
    try { r = await fetch(base + path, opt); } catch { throw errore(0, 'Connessione assente, riprova'); }
    if (r.status === 429) throw errore(429, 'Troppi tentativi, riprova tra poco');
    if (r.status === 401 && sessione) { salva(null); throw errore(401, 'Sessione scaduta, accedi di nuovo'); }
    const dati = r.status === 204 ? null : await r.json().catch(() => null);
    if (!r.ok) throw errore(r.status, (dati && dati.message) || `Errore ${r.status}`);
    return dati;
  }

  const rec = (c, id = '') => `/api/collections/${encodeURIComponent(c)}/records${id ? '/' + encodeURIComponent(id) : ''}`;

  return {
    utente: () => (sessione ? sessione.record : null),
    async login(email, password) {
      try {
        const d = await chiama('/api/collections/users/auth-with-password', {
          method: 'POST', body: { identity: email, password }, auth: false,
        });
        salva({ token: d.token, record: d.record });
      } catch (e) {
        if (e.status === 400) throw errore(400, 'Email o password non corretti');
        throw e;
      }
    },
    logout: () => salva(null),
    elenco(c, { filter, sort = '-created', perPage = 50 } = {}) {
      const q = new URLSearchParams({ sort, perPage: String(perPage) });
      if (filter) q.set('filter', filter);
      return chiama(`${rec(c)}?${q}`);
    },
    crea: (c, dati) => chiama(rec(c), { method: 'POST', body: dati }),
    modifica: (c, id, dati) => chiama(rec(c, id), { method: 'PATCH', body: dati }),
    cancella: (c, id) => chiama(rec(c, id), { method: 'DELETE' }),
  };
}
