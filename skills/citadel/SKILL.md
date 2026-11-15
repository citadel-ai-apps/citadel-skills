---
name: citadel
description: Entry point for Citadel, the company platform that hosts PocketBase apps. Explains what you can do and points to the right skill. Use it when the user asks what Citadel is, what it can do, how to get access, how to create, publish or change an app, or when it is unclear which step to start from.
---

# Citadel

Citadel hosts the company's internal apps. Each app has its own data, a web page and its own address. It runs isolated from the others, and can reach the outside only where that has been authorised. Whoever creates an app does not need to know how to code: they describe what they need, and the skills do the rest.

**Language**: talk to the user in the user's language (the `language` setting if there is one, otherwise the language they write in). Skill names, commands and file names stay as they are.

**Tone: terse.** Answer with the steps below, then ask where to start.

## The steps

| I want to… | Skill | Needs |
|---|---|---|
| connect to Citadel | `citadel-connect` | portal address and token, from the operator |
| create a new app | `citadel-interview`, then `citadel-new-app`, then `citadel-publish` | an idea; the app's short name, created by the operator |
| change an app | `citadel-edit-app` | the app's working folder |
| republish an app | `citadel-publish` | the app's working folder |

The interview also works without a connection to Citadel. Building and publishing need an agent that works on the computer, such as Claude Code or Codex.

## Who does what

- **The user** describes the app, tries it, publishes it and changes it.
- **The Citadel operator** creates new apps, hands out tokens and approves the connections that are not automatic: a service given with a wildcard, sending email, a custom address.
- **Citadel** records every publication and every authorisation. If a publication fails, it puts the previous version back online by itself.

## Where to start

Read the configuration with `python3 <citadel-connect folder>/connect.py check`:
- if it is missing, the portal does not answer or the token is not valid, start from `citadel-connect`, which collects the details with guided questions;
- if it is there, show the known apps with `connect.py apps` and ask whether to create a new one or change one.
