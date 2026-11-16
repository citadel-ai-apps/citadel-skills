# PocketBase on Citadel

JS API of PocketBase 0.23 and later (the versions Citadel offers for these apps are 0.38, 0.40, 0.41 and 0.42). Official docs: https://pocketbase.io/docs/js-overview/

Collection names, field names and identifiers are in English. Text the app's users read is in the spec's `Language`.

## Migrations

One file per step, `pb_migrations/<unix timestamp>_<what>.js`. Files are applied in name order, once. A migration already published is never edited: to change something, add a new one.

```js
migrate((app) => {
    const users = app.findCollectionByNameOrId("users");
    const items = new Collection({
        type: "base",
        name: "items",
        listRule: "owner = @request.auth.id",
        viewRule: "owner = @request.auth.id",
        createRule: '@request.auth.id != "" && @request.body.owner = @request.auth.id',
        updateRule: "owner = @request.auth.id && @request.body.owner:isset = false",
        deleteRule: "owner = @request.auth.id",
        fields: [
            { name: "owner", type: "relation", required: true, collectionId: users.id, maxSelect: 1, cascadeDelete: true },
            { name: "title", type: "text", required: true, max: 200 },
            { name: "status", type: "select", values: ["open", "closed"], maxSelect: 1 },
            { name: "created", type: "autodate", onCreate: true, onUpdate: false },
            { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
        ],
        indexes: ["CREATE INDEX idx_items_owner ON items (owner, created)"],
    });
    app.save(items);
}, (app) => {
    app.delete(app.findCollectionByNameOrId("items"));
});
```

- Field types: `text`, `number`, `bool`, `email`, `url`, `date`, `autodate`, `select` (`values`, `maxSelect`), `relation` (`collectionId`, `maxSelect`, `cascadeDelete`), `file` (`maxSelect`, `maxSize` in bytes, `mimeTypes`), `json`, `editor`.
- `created` and `updated` must be declared as `autodate` fields: a collection created from code does not have them by itself.
- `select` values are stored data: keep them short English keys (`open`, `closed`) and show translated labels on the pages.

### Rules

| Value | Meaning |
|---|---|
| `null` | nobody through the API, only the owner from the `/_/` panel |
| `""` | anyone, even without an account |
| `@request.auth.id != ""` | anyone who has signed in |
| `field = @request.auth.id` | only the entry's owner |
| `@request.auth.role = "manager"` | only people with that role (field on the `users` collection) |

On create, `@request.body.owner = @request.auth.id` stops people creating entries in someone else's name. On update, `@request.body.owner:isset = false` stops the owner being changed.

### Users and proxy

If the app has users, always add this migration. Sign-in follows the spec: here it is by invitation.

```js
migrate((app) => {
    const users = app.findCollectionByNameOrId("users");
    users.createRule = null;                 // by invitation; "" for open sign-up
    users.passwordAuth.enabled = true;
    users.passwordAuth.identityFields = ["email"];
    users.oauth2.enabled = false;
    users.otp.enabled = false;
    users.mfa.enabled = false;
    app.save(users);

    // All requests come from Citadel's proxy, which appends the real IP
    // to X-Forwarded-For. Without these two lines the rate limit sees a
    // single client for everyone.
    const settings = app.settings();
    settings.trustedProxy.headers = ["X-Forwarded-For"];
    settings.trustedProxy.useLeftmostIP = false;
    settings.rateLimits.enabled = true;
    app.save(settings);
}, (app) => {
    const users = app.findCollectionByNameOrId("users");
    users.createRule = "";
    app.save(users);
});
```

A `role` field is added with `users.fields.add(new SelectField({ name: "role", values: [...], maxSelect: 1 }))`. To stop users giving themselves a role, the `users` `updateRule` must contain `@request.body.role:isset = false`.

## Hooks

Files `pb_hooks/*.pb.js`. **Each handler runs in an isolated context**: variables and functions declared outside the handler are not visible inside it. Constants are declared inside the handler. Shared code goes in a CommonJS module, `pb_hooks/lib.js` with `module.exports = {...}`, loaded inside the handler with `require(`${__hooks}/lib.js`)`.

```js
routerAdd("GET", "/api/weather", (e) => {
    const city = e.request.url.query().get("city");
    if (!/^[A-Za-zÀ-ú ]{2,40}$/.test(city)) throw new BadRequestError("invalid city");

    const url = "https://api.example.com/v1/weather?q=" + encodeURIComponent(city);
    const hit = $app.store().get(url);
    if (hit && Date.now() - hit.t < 600000) return e.json(200, hit.body);

    let r;
    try {
        r = $http.send({ url: url, method: "GET", timeout: 15 });
    } catch (err) {
        throw new ApiError(502, "weather service unreachable", null);
    }
    if (r.statusCode !== 200) throw new ApiError(502, "the weather service answered " + r.statusCode, null);
    $app.store().set(url, { t: Date.now(), body: r.json });
    return e.json(200, r.json);
}, $apis.requireAuth());
```

- **Routes**: `routerAdd(method, path, handler, ...middleware)`. `$apis.requireAuth()` requires sign-in. Inside the handler: `e.auth` is the user, `e.requestInfo().body` the body, `e.request.url.query().get(k)` the parameters.
- **Errors**: `BadRequestError`, `UnauthorizedError`, `ForbiddenError`, `NotFoundError`, `ApiError(status, message, data)`. Messages the user will see go in the app's language.
- **External connections**: the host is always in the hook's code, never in a browser parameter. Validate input against fixed lists or strict expressions, set a `timeout`, and turn errors into 502 with a readable message. The host must be declared in `egress`.
- **Record events**: `onRecordCreateRequest((e) => { ...; e.next(); }, "items")`. Always call `e.next()`.
- **Queries**: `$app.findRecordsByFilter("items", "status = {:s}", "-created", 50, 0, { s: "open" })`. Always pass values as `{:name}` parameters, never concatenated into the filter.
- **Scheduled jobs**: `cronAdd("name", "0 * * * *", () => { ... })`.

### Access keys

Citadel does not pass environment variables to the app. Keys go in a `settings` collection (`key`, `value`) with every rule set to `null`. The owner fills it in from the `/_/` panel (on Citadel, opened from the app's page in the portal), and the hook reads it with `$app.findFirstRecordByData("settings", "key", "weather").get("value")`. The value never appears in the package or in the spec.

## Pages

- In `pb_public/`: an `index.html` and ES modules (`<script type="module">`). No build and no external libraries, unless a real need is written in the spec.
- **Pure logic in separate modules**, without the DOM. `fetch` and `localStorage` are passed in as parameters, so `node --test` tests can replace them with fakes. The client in [template/pkg/pb_public/api.js](template/pkg/pb_public/api.js) is the starting point; its user-facing `messages` are passed in the app's language.
- REST API:
  - list `GET /api/collections/<c>/records?filter=…&sort=-created&perPage=50`
  - create `POST`, update `PATCH /records/<id>`, delete `DELETE /records/<id>`
  - sign-in `POST /api/collections/users/auth-with-password` with `{identity, password}`, which returns `{token, record}`
  - later calls send the `Authorization: <token>` header
- The layout starts from the phone (360px wide) and uses the spec's language, also in `<html lang>`. Every state has its own message: loading, empty list, network error, session expired, too many attempts (429).

## Look

All colours live in CSS variables on `:root`, as in the template: an app's style changes in one place.

- **Company style**: the spec's colours go in `--accent` (primary) and, if present, `--accent-2`. The logo goes in `pb_public/` and appears in the header. The company font is loaded from a file in `pb_public/` (not from external services), or the system font is used. If colours or logo are "to collect", use the template's neutral style and say so in the closing message.
- **Theme**: "follows the computer" means `@media (prefers-color-scheme: dark)`. The switch sets `data-theme="light|dark"` on `<html>`, which wins over the system, and remembers the choice in `localStorage` (inside a `try`). "Light only" or "dark only" means a single set of variables.
- In both themes text must stay readable on the company colour: if the primary colour is light, the text on it is dark, and vice versa.
- **`brand` in the Citadel configuration** (the file `connect.py check` points to): when present, it is the default company style. It holds `logo`, `favicon` and `font.file` (local paths: copy the files into `pb_public/`), plus two palettes, `light` and `dark`, with the keys `bg`, `card`, `line`, `fg`, `muted`, `accent`, `on_accent`, `accent2`, `ok`, `warn`, `error`, `charts` (the series colours, in order) and `radius_px`. Older configurations use Italian names for some keys: `chiaro` = `light`, `scuro` = `dark`, `grafici` = `charts`, `raggio_px` = `radius_px`; read them the same way. Each key goes into the template's CSS variable of the same name: `on_accent` becomes `--on-accent`, `accent2` becomes `--accent-2`. The `charts` colours are used in the given order.

## Local run

Download PocketBase for the user's system from https://github.com/pocketbase/pocketbase/releases (the same minor version as the manifest: `darwin_arm64` or `darwin_amd64` on Mac, `windows_amd64` on Windows), unzip it into the app folder (download it yourself with `curl` on Mac or `Invoke-WebRequest` on Windows: on Mac a binary downloaded from the browser is blocked by Gatekeeper), then run from there, on one line (Windows: `.\pocketbase.exe` in place of `./pocketbase`):

```sh
./pocketbase serve --http 127.0.0.1:8090 --dir .pb-data --migrationsDir pkg/pb_migrations --hooksDir pkg/pb_hooks --publicDir pkg/pb_public
./pocketbase superuser upsert <email> <password> --dir .pb-data
```

The second command creates the account to enter `/_/` and add test users. This is for the local run only: on Citadel the owner enters `/_/` from the portal, without a password. `.pb-data` holds only local test data: keep it and the binary out of `pkg/`, and add both to `.gitignore` if the folder is a git repo. The app opens at http://127.0.0.1:8090.

Locally, outbound internet access is open. The run proves that migrations, hooks and pages work, not that the `egress` hosts will be authorised.
