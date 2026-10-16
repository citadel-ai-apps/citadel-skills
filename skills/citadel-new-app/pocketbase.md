# PocketBase su Citadel

API JS di PocketBase 0.23 e successive (le versioni offerte da Citadel sono 0.38 e 0.40). Documentazione ufficiale: https://pocketbase.io/docs/js-overview/

## Migrazioni

Un file per passo, `pb_migrations/<timestamp unix>_<cosa>.js`. I file vengono applicati in ordine di nome, una volta sola. Una migrazione già pubblicata non si modifica: per cambiare qualcosa se ne aggiunge una nuova.

```js
migrate((app) => {
    const users = app.findCollectionByNameOrId("users");
    const voci = new Collection({
        type: "base",
        name: "voci",
        listRule: "autore = @request.auth.id",
        viewRule: "autore = @request.auth.id",
        createRule: '@request.auth.id != "" && @request.body.autore = @request.auth.id',
        updateRule: "autore = @request.auth.id && @request.body.autore:isset = false",
        deleteRule: "autore = @request.auth.id",
        fields: [
            { name: "autore", type: "relation", required: true, collectionId: users.id, maxSelect: 1, cascadeDelete: true },
            { name: "titolo", type: "text", required: true, max: 200 },
            { name: "stato", type: "select", values: ["aperta", "chiusa"], maxSelect: 1 },
            { name: "created", type: "autodate", onCreate: true, onUpdate: false },
            { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
        ],
        indexes: ["CREATE INDEX idx_voci_autore ON voci (autore, created)"],
    });
    app.save(voci);
}, (app) => {
    app.delete(app.findCollectionByNameOrId("voci"));
});
```

- Tipi di campo: `text`, `number`, `bool`, `email`, `url`, `date`, `autodate`, `select` (`values`, `maxSelect`), `relation` (`collectionId`, `maxSelect`, `cascadeDelete`), `file` (`maxSelect`, `maxSize` in byte, `mimeTypes`), `json`, `editor`.
- `created` e `updated` vanno dichiarati come campi `autodate`: una collezione creata da codice non li ha di suo.

### Regole

| Valore | Significato |
|---|---|
| `null` | nessuno tramite API, solo il proprietario dal pannello `/_/` |
| `""` | chiunque, anche senza account |
| `@request.auth.id != ""` | chiunque abbia fatto l'accesso |
| `campo = @request.auth.id` | solo il proprietario della voce |
| `@request.auth.ruolo = "responsabile"` | solo chi ha quel ruolo (campo sulla collezione `users`) |

Sulla creazione, `@request.body.autore = @request.auth.id` impedisce di creare voci a nome di altri. Sulla modifica, `@request.body.autore:isset = false` impedisce di cambiare il proprietario.

### Utenti e proxy

Se l'app ha utenti, aggiungi sempre questa migrazione. L'ingresso si adatta alla scheda: qui è su invito.

```js
migrate((app) => {
    const users = app.findCollectionByNameOrId("users");
    users.createRule = null;                 // su invito; "" per l'iscrizione libera
    users.passwordAuth.enabled = true;
    users.passwordAuth.identityFields = ["email"];
    users.oauth2.enabled = false;
    users.otp.enabled = false;
    users.mfa.enabled = false;
    app.save(users);

    // Le richieste arrivano tutte dal proxy di Citadel, che aggiunge l'IP vero
    // in coda a X-Forwarded-For. Senza queste due righe il rate limit vede un
    // solo client per tutti.
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

Un campo `ruolo` si aggiunge con `users.fields.add(new SelectField({ name: "ruolo", values: [...], maxSelect: 1 }))`. Per impedire che un utente si assegni un ruolo da solo, la `updateRule` di `users` deve contenere `@request.body.ruolo:isset = false`.

## Hook

File `pb_hooks/*.pb.js`. **Ogni handler gira in un contesto isolato**: variabili e funzioni dichiarate fuori dall'handler non sono visibili dentro. Le costanti si dichiarano dentro l'handler. Il codice condiviso va in un modulo CommonJS, `pb_hooks/lib.js` con `module.exports = {...}`, caricato dentro l'handler con `require(`${__hooks}/lib.js`)`.

```js
routerAdd("GET", "/api/meteo", (e) => {
    const citta = e.request.url.query().get("citta");
    if (!/^[A-Za-zÀ-ú ]{2,40}$/.test(citta)) throw new BadRequestError("città non valida");

    const url = "https://api.esempio.it/v1/meteo?q=" + encodeURIComponent(citta);
    const hit = $app.store().get(url);
    if (hit && Date.now() - hit.t < 600000) return e.json(200, hit.body);

    let r;
    try {
        r = $http.send({ url: url, method: "GET", timeout: 15 });
    } catch (err) {
        throw new ApiError(502, "servizio meteo non raggiungibile", null);
    }
    if (r.statusCode !== 200) throw new ApiError(502, "il servizio meteo ha risposto " + r.statusCode, null);
    $app.store().set(url, { t: Date.now(), body: r.json });
    return e.json(200, r.json);
}, $apis.requireAuth());
```

- **Rotte**: `routerAdd(metodo, percorso, handler, ...middleware)`. `$apis.requireAuth()` chiede l'accesso. Dentro l'handler: `e.auth` è l'utente, `e.requestInfo().body` il corpo, `e.request.url.query().get(k)` i parametri.
- **Errori**: `BadRequestError`, `UnauthorizedError`, `ForbiddenError`, `NotFoundError`, `ApiError(stato, messaggio, dati)`.
- **Collegamenti esterni**: l'host sta sempre nel codice dell'hook, mai in un parametro del browser. Valida l'input contro liste fisse o espressioni strette, metti un `timeout`, e trasforma gli errori in 502 con un messaggio leggibile. L'host va dichiarato in `egress`.
- **Eventi sui record**: `onRecordCreateRequest((e) => { ...; e.next(); }, "voci")`. Chiama sempre `e.next()`.
- **Query**: `$app.findRecordsByFilter("voci", "stato = {:s}", "-created", 50, 0, { s: "aperta" })`. Passa sempre i valori come parametri `{:nome}`, mai concatenati nel filtro.
- **Lavori pianificati**: `cronAdd("nome", "0 * * * *", () => { ... })`.

### Chiavi d'accesso

Citadel non passa variabili d'ambiente all'app. Le chiavi vanno in una collezione `impostazioni` (`chiave`, `valore`) con tutte le regole a `null`. Il proprietario la compila dal pannello `/_/`, e l'hook la legge con `$app.findFirstRecordByData("impostazioni", "chiave", "meteo").get("valore")`. Il valore non compare mai nel pacchetto né nella scheda.

## Pagine

- In `pb_public/`: un `index.html` e moduli ES (`<script type="module">`). Niente build e niente librerie esterne, salvo necessità reali scritte nella scheda.
- **Logica pura in moduli separati**, senza DOM. `fetch` e `localStorage` si passano come parametri, così i test con `node --test` li sostituiscono con versioni finte. Il client in [template/pkg/pb_public/api.js](template/pkg/pb_public/api.js) è il punto di partenza.
- API REST:
  - elenco `GET /api/collections/<c>/records?filter=…&sort=-created&perPage=50`
  - creazione `POST`, modifica `PATCH /records/<id>`, cancellazione `DELETE /records/<id>`
  - accesso `POST /api/collections/users/auth-with-password` con `{identity, password}`, che restituisce `{token, record}`
  - le chiamate successive mandano l'header `Authorization: <token>`
- Il layout parte dal telefono (larghezza da 360px) e usa la lingua della scheda. Ogni stato ha il suo messaggio: caricamento, lista vuota, errore di rete, sessione scaduta, troppi tentativi (429).

## Aspetto

Tutti i colori stanno in variabili CSS su `:root`, come nel template: lo stile di un'app si cambia in un punto solo.

- **Stile aziendale**: i colori della scheda vanno in `--accent` (principale) e, se c'è, `--accent-2`. Il logo va in `pb_public/` e compare nell'intestazione. Il carattere aziendale si carica da un file in `pb_public/` (non da servizi esterni) oppure si usa quello di sistema. Se colori o logo sono "da raccogliere", usa lo stile neutro del template e segnalalo nella chiusura.
- **Tema**: "segue il computer" vuol dire `@media (prefers-color-scheme: dark)`. L'interruttore aggiunge `data-theme="light|dark"` su `<html>`, che ha la precedenza sul sistema, e ricorda la scelta in `localStorage` (dentro un `try`). "Solo chiaro" o "solo scuro" vuol dire un solo insieme di variabili.
- In entrambi i temi il testo deve restare leggibile sul colore aziendale: se il colore principale è chiaro, il testo sopra è scuro, e viceversa.
- `brand` in `~/.config/citadel/config.json` ha la forma `{"nome": "...", "accent": "#0F4C81", "accent2": "#C24A0B", "logo": "/percorso/logo.svg", "font": "..."}`: quando c'è, è lo stile aziendale predefinito.

## Prova in locale

Scarica PocketBase per il tuo sistema da https://github.com/pocketbase/pocketbase/releases (la stessa versione minore del manifest), poi:

```sh
pocketbase serve --http 127.0.0.1:8090 --dir /tmp/<nome>-pb \
  --migrationsDir <nome>/pkg/pb_migrations --hooksDir <nome>/pkg/pb_hooks --publicDir <nome>/pkg/pb_public
pocketbase superuser upsert <email> <password> --dir /tmp/<nome>-pb   # per entrare in /_/ e creare utenti di prova
```

In locale l'uscita verso internet è libera. La prova dimostra che migrazioni, hook e pagine funzionano, non che gli host di `egress` saranno autorizzati.
