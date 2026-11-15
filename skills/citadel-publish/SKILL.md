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

- **Target app**: the spec's "Short name" (`<name>/spec.md`; in an older app, "Nome breve" in `<name>/scheda.md`). The operator creates it: if the API answers 404 on the app, tell the user and stop.
- **Version**: increase `version` in `pbapp.json` over the last one published.
- **Check**: `python3 <citadel-new-app folder>/check_package.py <name>/pkg` must answer `ok`.

## 3. Publication

```sh
python3 <this skill's folder>/publish.py <name>/pkg --tenant <short name>
```

The script builds a reproducible zip, uploads it, starts the deploy and reads the state of the connections. It returns JSON and exits with 0 only if the deploy succeeded. With `--dry-run` it shows the zip's contents without uploading anything.

Citadel's deploy follows this sequence: data snapshot, version swap, health check, `smoke` requests. If a step fails, Citadel goes back to the previous version by itself, code and data (`rolled_back: true`).

## 4. Result

A short message to the user:

- **Succeeded**: the app's `address` and how people get in, according to the spec's Sign-in section. For example: "you create users from the `/_/` panel", or "just open the link".
- **Connections**: for each host in `grants`, authorised or pending. A pending host (Tier 2) must be approved by the operator in the portal, on the authorisations page; until then calls to that host fail and the app must show a clear message.
- **Failed**: which step (`failed_step`), the reason in plain words, and that the previous version is still online. Then fix it with `citadel-new-app` starting from `error` and `log`, and publish again.
