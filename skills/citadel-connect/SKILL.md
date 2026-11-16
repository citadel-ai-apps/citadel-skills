---
name: citadel-connect
description: Connects this computer to a Citadel installation - portal address, personal token, the apps you can access. Use it when Citadel has to be set up, when another Citadel skill finds the configuration missing or the token invalid, or when the user asks how to access Citadel or which apps they have.
---

# Connecting to Citadel

**Language**: talk to the user in the user's language (the `language` setting if there is one, otherwise the language they write in). Commands, keys and file names stay in English.

**Tone: terse.** What is needed, the command to run, the result.

All Citadel skills read the same configuration, managed by `connect.py` (in this skill's folder). Each project can have its own environment:
- **read**: the nearest `.citadel/config.json` wins, from the current folder up to the root of the git repo; if there is none, `~/.config/citadel/config.json` (global);
- **write**: `init` creates `.citadel/config.json` at the repo root (outside git, in the current folder) and adds `.citadel/` to `.gitignore`; `set-token` and `add-app` write to the project file and stop if it is missing. With `--global` all three use the global file;
- the `CITADEL_CONFIG` variable, when set, wins over everything.

`check` always reports which file it is using (`file`, `scope`).

## First time on this computer

When `check` finds no configuration at all, follow the tutorial in [first-time.md](first-time.md): asking the operator for the token, opening a terminal on Mac or Windows, entering the token. The sections below are the reference it relies on.

## 1. What is needed

From their company's Citadel operator the user receives:
- the **portal address**, for example `https://citadel.company.com`;
- the **apps domain**, for example `apps.company.com` (in development it may include the scheme: `http://apps.localhost`);
- a **personal token**;
- the **short name** of each app they can work on. New apps are created by the operator;
- a **portal password**, to open each app's PocketBase admin (`/_/`) from the portal.

## 2. Configuration

Start from `python3 connect.py check`, run in the project folder. If the configuration is missing, the portal does not answer or a value is wrong, collect the details with guided questions, not with a request in prose.

### Questions

- **With the multiple-choice question tool** (in Claude Code it is `AskUserQuestion`; other agents may have an equivalent): at most two questions per call, 2-4 options each with a short label and one line saying what it implies. Put the most sensible choice first, marked "(recommended)". The user can always type their own answer: remind them when no option can be the right one (an address you do not know).
- **Without the tool**: one question per message, numbered options below, and "or type it".

Build the options from what you already know: the `check` result (even an old global configuration), the apps found by `connect.py apps`, what the user has said. If a known value does not work, show it anyway with a note on the problem ("answers 401", "unreachable"), so the user recognises it.

Ask only what is missing or wrong, in this order:

1. **Where it applies** (and **portal**, in the same call):
   - "This project only (recommended)": the project's `.citadel/config.json`;
   - "All projects": the global one, with `--global` on each command below.
   For the portal: the known address, if any, plus "I'll type it" with an example (`https://citadel.company.com`).
2. **Apps domain** (and **apps**, in the same call):
   - for the domain, suggest what follows from the portal: the same host (`citadel.company.com`, apps are `<name>.citadel.company.com`) or `apps.` in front; plus the known one, if different;
   - for the apps, multiple choice: the known short names, plus "Another one: I'll type it". The short name comes from the operator, at most 10 characters.
3. **Token**: never as a question. It is a secret and must not go through the chat: see step 2 below.

Before writing, sum up in one line (where it applies, portal, domain, apps) and go ahead.

### Commands

1. `python3 connect.py init --url <portal> --apps-domain <domain>`
2. The user enters the token in a terminal window, where it is typed hidden: steps 3 and 4 of [first-time.md](first-time.md). `set-token` refuses to run from the chat's shell, which would show the token. If the user pastes it into the conversation, tell them to have it revoked and ask for a new one.
3. `python3 connect.py add-app <short name>` for each app.

## 3. Check

`python3 connect.py check --tenant <short name>`

The step is done when the portal is `reachable`, `token_valid` is `true` and every app exists. Otherwise go back to the questions only for the value that is wrong:
- portal unreachable: the address is wrong, or the company network or VPN is needed;
- token not valid: a new token has to be requested from the operator;
- app "does not exist, or you have no access to it": Citadel answers the same way in both cases. Ask the operator to create it, or to give your account a role on it (deployer, admin or owner to publish).

## 4. My apps

Citadel does not yet have a call that lists a user's apps. The known apps are therefore two sets:
- those registered with `add-app`;
- the working folders that contain `spec.md` (or `scheda.md`, for apps made with earlier versions of the skills) and `pkg/`.

`connect.py apps` shows them together: short name, local folder (if any), online release.

## 5. Getting an app's package back

`python3 connect.py download <short name> --dir <app folder>` downloads the package of the version online and unpacks it into `<app folder>/pkg` (`--release <id>` for another version). It needs the deployer role or above. The package holds the code only: the spec and the tests are not in it, `citadel-edit-app` rebuilds them.
