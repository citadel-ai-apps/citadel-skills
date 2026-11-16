// PocketBase REST client. No DOM: `fetch` and `storage` come from outside,
// so tests can replace them. In the browser:
//   createClient({ fetch: fetch.bind(window), storage: localStorage, messages: { ... } })
// `messages` holds the user-facing texts: pass them in the app's language (spec, `language`).

const MESSAGES = {
  offline: 'No connection, try again',
  tooMany: 'Too many attempts, try again shortly',
  expired: 'Session expired, sign in again',
  badLogin: 'Wrong email or password',
  error: (status) => `Error ${status}`,
};

function failure(status, message) {
  const e = new Error(message);
  e.status = status;
  return e;
}

export function createClient({ base = '', fetch, storage, key = 'session', messages = {} }) {
  const t = { ...MESSAGES, ...messages };
  // Storage may be missing or throw (private browsing): the session still lives in memory.
  let session = null;
  try { session = JSON.parse(storage.getItem(key)) || null; } catch { session = null; }

  function save(s) {
    session = s;
    try { s ? storage.setItem(key, JSON.stringify(s)) : storage.removeItem(key); } catch { /* memory only */ }
  }

  async function call(path, { method = 'GET', body, auth = true } = {}) {
    const headers = {};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (auth && session) headers.Authorization = session.token;
    const opt = { method, headers };
    if (body !== undefined) opt.body = JSON.stringify(body);
    let r;
    try { r = await fetch(base + path, opt); } catch { throw failure(0, t.offline); }
    if (r.status === 429) throw failure(429, t.tooMany);
    if (r.status === 401 && session) { save(null); throw failure(401, t.expired); }
    const data = r.status === 204 ? null : await r.json().catch(() => null);
    if (!r.ok) throw failure(r.status, (data && data.message) || t.error(r.status));
    return data;
  }

  const rec = (c, id = '') => `/api/collections/${encodeURIComponent(c)}/records${id ? '/' + encodeURIComponent(id) : ''}`;

  return {
    user: () => (session ? session.record : null),
    async login(email, password) {
      try {
        const d = await call('/api/collections/users/auth-with-password', {
          method: 'POST', body: { identity: email, password }, auth: false,
        });
        save({ token: d.token, record: d.record });
      } catch (e) {
        if (e.status === 400) throw failure(400, t.badLogin);
        throw e;
      }
    },
    logout: () => save(null),
    list(c, { filter, sort = '-created', perPage = 50 } = {}) {
      const q = new URLSearchParams({ sort, perPage: String(perPage) });
      if (filter) q.set('filter', filter);
      return call(`${rec(c)}?${q}`);
    },
    create: (c, data) => call(rec(c), { method: 'POST', body: data }),
    update: (c, id, data) => call(rec(c, id), { method: 'PATCH', body: data }),
    remove: (c, id) => call(rec(c, id), { method: 'DELETE' }),
  };
}
