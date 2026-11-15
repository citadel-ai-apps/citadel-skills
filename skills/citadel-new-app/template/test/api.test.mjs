import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createClient } from '../pkg/pb_public/api.js';

function memory() {
  const m = new Map();
  return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) };
}

// Fake fetch: answers from the `responses` queue and records the requests.
function fake(responses) {
  const requests = [];
  const f = async (url, opt = {}) => {
    requests.push({ url, method: opt.method || 'GET', headers: opt.headers || {}, body: opt.body ? JSON.parse(opt.body) : undefined });
    const [status, body] = responses.shift();
    return { ok: status >= 200 && status < 300, status, json: async () => body ?? {} };
  };
  f.requests = requests;
  return f;
}

test('login stores the session and uses it on later calls', async () => {
  const fetch = fake([[200, { token: 'T', record: { id: 'u1' } }], [200, { items: [] }]]);
  const storage = memory();
  const c = createClient({ fetch, storage });
  await c.login('a@b.it', 'x');
  assert.deepEqual(c.user(), { id: 'u1' });
  assert.deepEqual(createClient({ fetch, storage }).user(), { id: 'u1' }, 'persists in storage');
  await c.list('items');
  assert.equal(fetch.requests[1].url, '/api/collections/items/records?sort=-created&perPage=50');
  assert.equal(fetch.requests[1].headers.Authorization, 'T');
});

test('wrong login gives a single message', async () => {
  const c = createClient({ fetch: fake([[400, {}]]), storage: memory() });
  await assert.rejects(c.login('a@b.it', 'x'), { message: 'Wrong email or password' });
  assert.equal(c.user(), null);
});

test('messages can be replaced in the app language', async () => {
  const c = createClient({ fetch: fake([[400, {}]]), storage: memory(), messages: { badLogin: 'Email o password non corretti' } });
  await assert.rejects(c.login('a@b.it', 'x'), { message: 'Email o password non corretti' });
  const d = createClient({ fetch: fake([[429, {}]]), storage: memory(), messages: { badLogin: 'x' } });
  await assert.rejects(d.list('items'), { message: 'Too many attempts, try again shortly' }, 'missing keys keep the default');
});

test('401 with a session closes it', async () => {
  const fetch = fake([[200, { token: 'T', record: { id: 'u1' } }], [401, {}]]);
  const c = createClient({ fetch, storage: memory() });
  await c.login('a@b.it', 'x');
  await assert.rejects(c.list('items'), { status: 401 });
  assert.equal(c.user(), null);
});

test('network down and 429 have readable messages', async () => {
  const down = createClient({ fetch: async () => { throw new TypeError('failed'); }, storage: memory() });
  await assert.rejects(down.list('items'), { status: 0 });
  const many = createClient({ fetch: fake([[429, {}]]), storage: memory() });
  await assert.rejects(many.list('items'), { status: 429 });
});

test('a throwing storage does not block the client', async () => {
  const broken = { getItem() { throw new Error('no'); }, setItem() { throw new Error('no'); }, removeItem() { throw new Error('no'); } };
  const c = createClient({ fetch: fake([[200, { token: 'T', record: { id: 'u1' } }]]), storage: broken });
  await c.login('a@b.it', 'x');
  assert.deepEqual(c.user(), { id: 'u1' });
});
