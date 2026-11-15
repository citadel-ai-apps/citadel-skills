---
name: citadel-new-app
description: Builds a new app for Citadel from its spec. Produces the PocketBase package (migrations, hooks, pages) with tests, and checks it locally. Use it when an app for Citadel has to be created or built, or when a spec in `<name>/spec.md` is ready to be built.
---

# Building an app for Citadel

Citadel hosts PocketBase apps. Each app is a **package**: migrations for the data, hooks for server-side logic, static pages, a manifest. The platform supplies the rest (binary, network, backups). The package can be written in any folder: the Citadel repo is not needed.

## Language

- **Conversation**: in the user's language (the `language` setting if there is one, otherwise the language they write in).
- **App**: everything the app's users read (pages, buttons, messages, empty states, sample data, `<html lang>`) is in the spec's `Language`. An old `scheda.md` without that field means Italian.
- **Code**: file names, collection and field names, identifiers and comments in English.

**Tone: terse** with the user: short sentences, lists, technical detail only if they ask.

## App folder

```
<name>/
  spec.md        what to build and why (from citadel-interview); older apps: scheda.md
  pkg/           the package: pbapp.json, pb_migrations/, pb_hooks/, pb_public/
  test/          *.test.mjs, run with node --test
```

## 1. Spec

Read `<name>/spec.md` (or `<name>/scheda.md` for an older app). If there is no spec, run the interview with `citadel-interview` first.

Then go through the two lists at the end of the spec:
- **Information to collect**: ask the user for the items needed to build now, one per message. An item nobody has (for example an API's documentation) becomes a clearly marked stub in the code and an item in the closing message.
- **To decide**: every point that changes the code is settled now. Propose a choice in one line and ask for confirmation.

Every decision taken here is written into the spec, in the section it concerns.

## 2. Plan

Show the plan in no more than eight lines: collections, screens, connections, files you will create. Ask "shall I go ahead?" and wait for the yes.

## 3. Build

Start from [template/](template/): copy `pkg/` and `test/` into the app folder, replace `NAME`, and create `pb_migrations/` and `pb_hooks/` when needed. If the app's language is not English, set `<html lang>` and pass `messages` to `createClient` in that language (see [api.js](template/pkg/pb_public/api.js)). Then, in this order:

1. **Migrations**: one collection per row of the spec's Data table, with rules that reproduce exactly the "who sees / who creates / who edits" columns. Every rule must trace back to the spec.
2. **Hooks**: only for external connections and for logic the browser must not see.
3. **Pages**: the screens in the Interface section, in the spec's words and language, with the style in the Look section (see [pocketbase.md](pocketbase.md#look)).
4. **Manifest**: `name`, `version`, `egress` (one host per connection), the `smoke` requests.

Before writing migrations or hooks, read [pocketbase.md](pocketbase.md): the correct syntax, the patterns already proven on Citadel and the most common mistakes. The package format rules are in [package.md](package.md).

## 4. Check

The step is done when all three checks pass:

1. `node --test '<name>/test/*.test.mjs'` is green.
2. `python3 <this skill's folder>/check_package.py <name>/pkg` answers `ok`.
3. **Local run**, if `pocketbase` is installed: start it on the package (command in [pocketbase.md](pocketbase.md#local-run)). Every `smoke` request in the manifest must answer with its `expectStatus`. If `pocketbase` is not there, ask the user whether to download it; if they say no, mark the run as not done.

Fix and repeat until they pass.

## 5. Closing

A short message:
- what you built: collections, screens, connections;
- how to try it locally, if you started it;
- what is missing: stubs, information that did not arrive, checks not done;
- the next step: publish it on Citadel with `citadel-publish`.
