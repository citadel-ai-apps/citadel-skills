---
name: citadel-publish
description: Publishes an app already built for Citadel. Uploads the package, deploys it, returns the address and the state of the external connections. Use it when a Citadel app has to be published, put online, updated or released.
---

# Publishing an app on Citadel

**Language**: talk to the user in the user's language (the `language` setting if there is one, otherwise the language they write in). Commands and JSON keys stay in English.

**Tone: terse** with the user: result, address, what is left to do.

## 1. Configuration

Three values are needed: the Citadel portal address (`url`), a personal token (`token`), the apps domain (`apps_domain`, for example `apps.company.com`; in development it may include the scheme, `http://apps.localhost`). The script reads them from the variables `CITADEL_URL`, `CITADEL_TOKEN` and `CITADEL_APPS_DOMAIN`, or from the `citadel-connect` configuration file: the project one (`.citadel/config.json`, the nearest going up from the package folder to the repo root) or, if missing, the global one (`~/.config/citadel/config.json`).

If they are missing, use `citadel-connect`. The **token is saved by the user**: they get it from the Citadel operator and type it hidden with `connect.py set-token`. Its value stays out of the chat and out of every output.

## 2. Package and app

- **Target app**: the spec's "Short name" (`<name>/spec.md`; in an older app, "Nome breve" in `<name>/scheda.md`). The operator creates it and gives the user a role on it. A 404 means the app does not exist or the user has no access to it, a 403 that their role cannot publish: tell the user what to ask the operator (the script's `hint`) and stop.
- **Version**: increase `version` in `pbapp.json` over the last one published.
- **Check**: `python3 <citadel-new-app folder>/check_package.py <name>/pkg` must answer `ok`.
- **Seen locally**: the user has seen this version running on their computer (step 5 of `citadel-new-app`). If not, show it first.

## 3. Publication

```sh
python3 <this skill's folder>/publish.py <name>/pkg --tenant <short name>
```

The script builds a reproducible zip, uploads it, starts the deploy and reads the state of the connections. It returns JSON and exits with 0 only if the deploy succeeded. With `--dry-run` it shows the zip's contents without uploading anything.

Citadel's deploy follows this sequence: data snapshot, version swap, health check, `smoke` requests. If a step fails, Citadel goes back to the previous version by itself, code and data (`rolled_back: true`).

## 4. Result

A short message to the user:

- **Succeeded**: the app's `address` and how people get in, according to the spec's Sign-in section. For example: "sign in to the Citadel portal, open the app's page, press *Open PocketBase admin* and create the users there", or "just open the link". Settings such as access keys are filled in the same way.
- **Connections**: for each host in `grants`, authorised or pending. A pending host (Tier 2) must be approved by the operator in the portal, on the authorisations page; until then calls to that host fail and the app must show a clear message.
- **Failed**, three cases:
  - `rolled_back: true` (`failed_step` is `verify`): the new version did not start, or the health check or a `smoke` request failed. Citadel put the previous version back, code and data. Explain `error` in plain words, then fix it with `citadel-new-app` starting from `error` and `log`.
  - `rolled_back: false` and no `failed_step`: Citadel refused the version before touching anything, for example the app's PocketBase version is outside the `pocketbase` range, or an `egress` host can never be granted. The previous version is still online.
  - `ok: false` with `step` (`upload` or `deploy`), and often a `hint`: the package was refused on upload (the reason names the file), or the request itself was refused (access, app busy with an upgrade or frozen by an operator). Nothing changed online.

  Then publish again.
