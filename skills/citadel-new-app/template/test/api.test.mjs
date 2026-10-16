import { test } from 'node:test';
import assert from 'node:assert/strict';
import { creaClient } from '../pkg/pb_public/api.js';

function memoria() {
  const m = new Map();
  return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) };
}

// fetch finto: risponde con la coda `risposte` e registra le richieste.
function finto(risposte) {
  const richieste = [];
  const f = async (url, opt = {}) => {
    richieste.push({ url, method: opt.method || 'GET', headers: opt.headers || {}, body: opt.body ? JSON.parse(opt.body) : undefined });
    const [status, body] = risposte.shift();
    return { ok: status >= 200 && status < 300, status, json: async () => body ?? {} };
  };
  f.richieste = richieste;
  return f;
}

test('login salva la sessione e la usa nelle chiamate successive', async () => {
  const fetch = finto([[200, { token: 'T', record: { id: 'u1' } }], [200, { items: [] }]]);
  const storage = memoria();
  const c = creaClient({ fetch, storage });
  await c.login('a@b.it', 'x');
  assert.deepEqual(c.utente(), { id: 'u1' });
  assert.deepEqual(creaClient({ fetch, storage }).utente(), { id: 'u1' }, 'persiste nello storage');
  await c.elenco('voci');
  assert.equal(fetch.richieste[1].url, '/api/collections/voci/records?sort=-created&perPage=50');
  assert.equal(fetch.richieste[1].headers.Authorization, 'T');
});

test('login errato dà un messaggio unico', async () => {
  const c = creaClient({ fetch: finto([[400, {}]]), storage: memoria() });
  await assert.rejects(c.login('a@b.it', 'x'), { message: 'Email o password non corretti' });
  assert.equal(c.utente(), null);
});

test('401 con sessione la chiude', async () => {
  const fetch = finto([[200, { token: 'T', record: { id: 'u1' } }], [401, {}]]);
  const c = creaClient({ fetch, storage: memoria() });
  await c.login('a@b.it', 'x');
  await assert.rejects(c.elenco('voci'), { status: 401 });
  assert.equal(c.utente(), null);
});

test('rete assente e 429 hanno messaggi leggibili', async () => {
  const giu = creaClient({ fetch: async () => { throw new TypeError('failed'); }, storage: memoria() });
  await assert.rejects(giu.elenco('voci'), { status: 0 });
  const tanti = creaClient({ fetch: finto([[429, {}]]), storage: memoria() });
  await assert.rejects(tanti.elenco('voci'), { status: 429 });
});

test('storage che lancia non blocca il client', async () => {
  const rotto = { getItem() { throw new Error('no'); }, setItem() { throw new Error('no'); }, removeItem() { throw new Error('no'); } };
  const c = creaClient({ fetch: finto([[200, { token: 'T', record: { id: 'u1' } }]]), storage: rotto });
  await c.login('a@b.it', 'x');
  assert.deepEqual(c.utente(), { id: 'u1' });
});
