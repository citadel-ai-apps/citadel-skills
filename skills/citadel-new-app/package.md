# The Citadel package

## Contents

A zip that contains **only**:

```
pbapp.json       manifest
pb_migrations/   *.js     data schema, applied on deploy
pb_hooks/        *.js     server-side logic (*.pb.js loaded automatically, the others via require)
pb_public/       any static file, served at the site root
```

Citadel rejects the upload, naming the path at fault, when:
- there is a file outside these four entries;
- `pb_migrations/` or `pb_hooks/` contains a file that is not `.js`;
- a file is a symbolic link, has the executable or setuid bit, or is an absolute path or contains `..`;
- a path appears twice, or uses `\` as separator;
- it exceeds 50 MiB uncompressed or 2000 files, or the compression is suspicious (ratio above 200, checked above 1 MiB);
- the manifest is not valid (see below).

`check_package.py` checks all of this locally. For egress it knows only a few public suffixes, while Citadel checks the full list: a wildcard it accepts may still be refused on upload.

## Manifest (`pbapp.json`)

```json
{
  "schemaVersion": 1,
  "name": "room-booking",
  "version": "1.0.0",
  "pocketbase": { "min": "0.38.0", "max": "0.42.x" },
  "egress": ["api.example.com"],
  "healthcheck": { "path": "/api/health", "expectStatus": 200 },
  "smoke": [
    { "method": "GET", "path": "/", "expectStatus": 200 }
  ]
}
```

- `schemaVersion`: always `1`.
- `name`, `version`: printable text, at most 64 characters. Increase `version` on every publication.
- `pocketbase`: the range of compatible versions. `x` is allowed only after the major version (`0.42.x`); an absent bound is open. It must include at least one version the platform offers: today `0.38.2`, `0.40.4`, `0.41.1` and `0.42.2` (there is also `0.22.55`, but it has a different JS API and these skills do not use it). On deploy Citadel also checks that the target app's version, chosen by the operator when creating it, is inside the range: if not, the deploy is rejected. The range also gates runtime upgrades: Citadel will not move the app to a version above `max`, so keep `max` up to the newest version the app has been tried on.
- `egress`: the external hosts the app will call from the server, as lowercase host names (no scheme, port or path). It is a **request**: a precise host is authorised automatically, a wildcard (`*.example.com`) waits for an approver, and so does a precise host that was denied or revoked for this app before. Rejected outright: IP addresses (also in short forms like `10.1`), wildcards on a top-level domain or a public suffix (`*.co.uk`, `*.github.io`), names that never resolve publicly (`.local`, `.internal`, `.lan`, `.corp`, `.test`…), Citadel's own apps domain. Private networks are refused when the call is made. Empty or absent means no outbound internet access.
- `healthcheck`: default `GET /api/health` → 200.
- `smoke`: requests replayed after every deploy and in every upgrade rehearsal. Methods: `GET`, `HEAD`, `POST`, `PUT`, `PATCH`, `DELETE`; paths start with `/` and contain no `..`. If one fails, Citadel goes back to the previous version, code and data. Rehearsals run on a copy **without internet access**, so no smoke request may depend on an external host. Smoke requests run against the real data: a `POST` that succeeds creates a real entry. A path that does not exist still answers 200, because PocketBase returns `index.html`: a `GET` expecting 200 does not prove a file or route exists. For each hook route, add a case only the real route produces, such as an invalid parameter → 400 or a protected route without access → 401. For each collection, add the answer its rules impose: for example `GET /api/collections/<c>/records` without access → 200 with open rules, 403 with reading closed to everyone.

## Runtime

- **No environment variables** for the app: access keys are kept as described in [pocketbase.md](pocketbase.md#access-keys).
- **Network**: only the `egress` hosts already authorised. A call to a host waiting for approval fails, and the portal shows why.
- **Read-only filesystem**, except PocketBase's data. No shell: `$os.exec` and similar do not work.
- **Disk** with a per-app quota (2 GiB by default, set by the operator): `file` fields use it.
- **Request size**: 32 MB per request by default, cut at the Citadel proxy. A `file` field's `maxSize` stays below it.
- **Memory**: 256 MiB by default; keep hooks from loading large data sets at once.
- **Email**: not available today. PocketBase's mailer connects to the mail server directly, and Citadel blocks that. Verification emails, password resets by email and notifications do not leave the app.
- **Rate limits**: the Citadel proxy limits requests per client on `/api/` and `/_/`; the app shows the 429 message.
- The app answers at `https://<short name>.<apps domain>`, behind a Citadel proxy.
- **The `/_/` admin** is opened from the portal: the app's owner (or an admin) signs in to the portal and, on the app's page, presses "Open PocketBase admin". There is no superuser password to keep.
