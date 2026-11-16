---
name: citadel
description: Step-by-step wizard for Citadel, the company platform that hosts PocketBase apps - from an empty computer to an app online. Use it when the user wants to create an app on Citadel, asks how to start, what Citadel is or what to do next, or when it is unclear which Citadel skill comes next.
---

# Citadel wizard

Citadel hosts the company's internal apps. Each app has its own data, a web page and its own address, runs isolated from the others, and reaches the outside only where that has been authorised. Whoever creates an app does not need to code: they describe what they need, and the skills do the rest.

**Language**: talk to the user in the user's language (the `language` setting if there is one, otherwise the language they write in). Skill names, commands and file names stay as they are.

**Tone: terse and childproof.** The user may never have opened a terminal.

## How the wizard talks

- **One step per message**, headed "Step N of 7: <name>". At most two lines on what the step is for, in everyday words, then what to do.
- **You do the work you can**: run commands, check versions, create folders, call the other skills. The user does only what needs a person: choices, sending a message to the operator, typing the token, trying the app.
- **Copy blocks**: whenever the user has to type something, give it in a code block, one command per block, filled in with real values (absolute paths in double quotes, never a `<placeholder>`). On Mac the command is `python3`, on Windows `py` (or `python` if `py` is not recognised).
- **Mac or Windows, Claude or ChatGPT**: find out the system yourself (run a command) and give only the instructions for that system. Ask only when you cannot tell.
- **Resume**: every time the wizard starts, work out where the user is (steps 1-3 by checking, then which apps have `spec.md` and `pkg/`), say in one line what is already done and start from the first step that is not.

## The steps

### Step 1 of 7: tools

Check yourself: Python 3 (`python3 --version`, on Windows `py --version`) and Node.js 18 or later (`node --version`). If something is missing, offer to install it, or give the user the command:

| Missing | Mac | Windows (PowerShell) |
|---|---|---|
| Python 3 | download from python.org/downloads, open the file, click Continue to the end | `winget install -e --id Python.Python.3.12` |
| Node.js | download the LTS version from nodejs.org, open the file, click Continue to the end | `winget install -e --id OpenJS.NodeJS.LTS` |

After installing, the terminal and the agent app (Claude or Codex) must be closed and reopened. Done when both versions answer.

If you are a chat without access to the computer (claude.ai, ChatGPT in the browser), you cannot do steps 1-3 and 5-7. Do the interview (step 4), then tell the user to continue on the computer with Claude Code (the Code tab of the Claude desktop app) or Codex (from ChatGPT), with this plugin installed (README of the plugin).

### Step 2 of 7: work folder

One folder holds all the user's apps, one subfolder per app. Suggest `Documents/citadel-apps` in their home folder, create it, and work from there for the rest of the wizard. Done when the folder exists.

### Step 3 of 7: connect to Citadel

Use `citadel-connect`. The first time, it follows its tutorial: the user asks the operator for a token and types it hidden in a terminal. Done when `connect.py check` is green.

Waiting for the operator does not block the wizard: the interview (step 4) works without a connection. Come back here before step 7.

### Step 4 of 7: describe the app

Use `citadel-interview`: about ten guided questions, a summary in plain words, then the spec in `<app>/spec.md`. Done when the user has confirmed the summary and the spec is written.

### Step 5 of 7: build

Use `citadel-new-app`. The user confirms the plan; you build and run the checks. Done when its three checks pass.

### Step 6 of 7: try it

Start the app locally (`citadel-new-app`, local run) and give the user the address to open in the browser, as a link. Ask "Does it do what you expected?". Changes go back to step 5 and are tried again. Done when the user says yes.

### Step 7 of 7: publish

Use `citadel-publish`. Close with the app's address, how people get in, and any connection still waiting for the operator's approval.

## After the first app

- **Change an app**: `citadel-edit-app` (the user can just say "I want to change <app>").
- **Republish**: `citadel-publish`.
- **New app**: start again from step 4; steps 1-3 are done once per computer.

## Who does what

- **The user** describes the app, tries it, publishes it and changes it.
- **The Citadel operator** creates new apps, hands out tokens and approves the connections that are not automatic: a service given with a wildcard, sending email, a custom address.
- **Citadel** records every publication and every authorisation. If a publication fails, it puts the previous version back online by itself.
