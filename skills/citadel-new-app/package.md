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
- it exceeds 50 MiB uncompressed or 2000 files, or the compression is suspicious (ratio above 200);
- the manifest is not valid (see below).

`check_package.py` checks all of this locally.

## Manifest (`pbapp.json`)

```json
{
  "schemaVersion": 1,
  "name": "room-booking",
  "version": "1.0.0",
  "pocketbase": { "min": "0.38.0", "max": "0.41.x" },
  "egress": ["api.example.com"],
  "healthcheck": { "path": "/api/health", "expectStatus": 200 },
  "smoke": [
    { "method": "GET", "path": "/", "expectStatus": 200 }
  ]
}
```

- `schemaVersion`: always `1`.
- `name`, `version`: text, at most 64 characters. Increase `version` on every publication.
- `pocketbase`: the range of compatible versions. `x` is allowed only after the major version (`0.40.x`). It must include at least one version the platform offers: today `0.38.2`, `0.40.4` and `0.41.1` (there is also `0.22.55`, but it has a different JS API and these skills do not use it). On deploy Citadel also checks that the target app's version, chosen by the operator when creating it, is inside the range: if not, the deploy is rejected.
- `egress`: the external hosts the app will call from the server. It is a **request**: a precise host is authorised automatically, a wildcard (`*.example.com`) waits for an approver. IP addresses, wildcards on a top-level domain, private networks and platform domains are rejected. Empty or absent means no outbound internet access.
- `healthcheck`: default `GET /api/health` → 200.
- `smoke`: requests replayed after every deploy. If one fails, Citadel goes back to the previous version, code and data. A path that does not exist still answers 200, because PocketBase returns `index.html`: a `GET` expecting 200 does not prove a file or route exists. For each hook route, add a case only the real route produces, such as an invalid parameter → 400 or a protected route without access → 401. For each collection, add the answer its rules impose: for example `GET /api/collections/<c>/records` without access → 200 with open rules, 403 with reading closed to everyone.

## Runtime

- **No environment variables** for the app: access keys are kept as described in [pocketbase.md](pocketbase.md#access-keys).
- **Network**: only the `egress` hosts already authorised. A call to a host waiting for approval fails, and the portal shows why.
- **Read-only filesystem**, except PocketBase's data. No shell: `$os.exec` and similar do not work.
- **Disk** with a per-app quota: `file` fields use it.
- The app answers at `https://<short name>.<apps domain>`, behind a Citadel proxy.
