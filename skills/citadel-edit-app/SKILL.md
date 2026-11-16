---
name: citadel-edit-app
description: Changes an app that already exists on Citadel. Shows the available apps, finds out with a few questions what to change, updates spec and package, and republishes. Use it when the user wants to change, improve, fix or extend a Citadel app that already exists.
---

# Changing a Citadel app

## Language

- **Conversation**: in the user's language (the `language` setting if there is one, otherwise the language they write in).
- **App**: text the app's users read stays in the spec's `Language` (an old `scheda.md` without that field means Italian), unless the user asks to change it.
- **Code**: file names, collection and field names, identifiers in English. In an older app with Italian names, keep the existing names: renaming a collection or field means a migration and can lose data.

**Tone: terse** with the user, as in the interview: conversational questions, no technical terms.

## 1. Pick the app

`python3 <citadel-connect folder>/connect.py apps --dir <working folder>` lists the known apps: local folder, local version, online version. Show them to the user one per line and ask which one to change. If the configuration is missing, use `citadel-connect` first.

To change an app you need its **working folder**, with `spec.md` (or `scheda.md` in an older app) and `pkg/`. Citadel does not give back the code of a published app. If the folder is not there, tell the user and stop: the code has to be recovered from where it was saved, for example a git repository.

If the local version differs from the online one, ask which of the two is the good one before going on.

## 2. What to change

Read the spec, then ask "What would you like to change?". Ask at most three questions to understand the concrete case, guided as in `citadel-interview`: ready-made options with the multiple-choice tool, if there is one. Every change falls into one of these types, and each type has its consequence:

| Type | For example | Consequence |
|---|---|---|
| Look and text | colours, wording, field order | `pb_public/` only |
| New information | an extra field, a new kind of entry | a **new migration** |
| Who sees or changes what | a manager, shared entries | rules in a new migration |
| Connections | an external service, sending email | hook plus `egress`; Tier 2 waits for an approver |
| Information to remove | a field no longer needed | new migration; **that field's data is lost** |

## 3. Summary

In the conversation language:

```
**What changes**
- …

**What you'll see differently**
<2-4 lines: the walk-through only over the screens that change>

**What stays the same**: …
**Watch out**: … (data that is lost, connections to approve; or: nothing)
```

Ask for confirmation. If data is lost, an explicit yes on that point is needed.

## 4. Build

1. Update the spec: the sections touched, plus a line under `## Changes` (create the section if missing) with date and version. In an older `scheda.md`, keep its Italian headings and add the section as `## Modifiche`.
2. Apply the change following steps 3, 4 and 5 of `citadel-new-app`, with the same checks: the user sees the changed app running locally and says yes before it is republished. Two extra rules apply: migrations already published stay as they are, and the existing tests must stay green.
3. Increase `version` in `pbapp.json`: the third number for look and fixes (1.2.0 → 1.2.1), the second for everything else (1.2.1 → 1.3.0).

## 5. Publication

Publish with `citadel-publish` and close as described there. If the deploy fails, Citadel has already put the previous version back online, data included.
