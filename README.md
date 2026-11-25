# Citadel skills

Website: [try.citadel-ai-apps.workers.dev](https://try.citadel-ai-apps.workers.dev/?utm_source=github&utm_content=skills)

Skills to create apps to publish on Citadel, without the Citadel repo.

| Skill | Step |
|---|---|
| `citadel` | entry point: what you can do and where to start |
| `citadel-install` | installs Citadel for a trial, when there is none yet: local VM on a Mac, or a pilot on a Linux server |
| `citadel-connect` | connects the computer to Citadel: portal, token, known apps |
| `citadel-interview` | from the idea to the app's spec, with simple questions |
| `citadel-new-app` | from the spec to the PocketBase package, with tests and a local check |
| `citadel-publish` | from the package to the app online: upload, deploy, state of the connections |
| `citadel-edit-app` | changes to an existing app: what to change, spec, package, republication |

## Quick start

1. **Install the plugin** in Claude or in ChatGPT/Codex: section [Install](#install).
2. **Start the wizard**: in Claude Code type `/citadel`; in Codex write `Use the citadel skill`.
3. **Follow the steps.** The wizard works on Mac and Windows and goes from an empty computer to an app online: tools, work folder, connection with your token, interview, build, try, publish. It does the technical part; you choose, try and type your token.

You need a Citadel token: ask the person who installed Citadel in your company (the operator). The wizard tells you what to ask. No Citadel in your company yet? Tell the wizard: `citadel-install` sets one up on your Mac for a trial and writes a report you can send to the Citadel team.

The configuration is managed by `citadel-connect`. Each project can have its own environment in `.citadel/config.json`, at the repo root (excluded from git); if it is missing, the global one applies, `~/.config/citadel/config.json`. The `CITADEL_CONFIG` variable overrides both.

## Languages

The skills are written in English and talk to each person in their own language. Three languages are kept apart:

- **The skills**: always English (instructions, file names, keys, code).
- **The conversation**: the user's. Claude Code reads it from the `language` setting in your own `~/.claude/settings.json`; without it, the skills answer in the language you write in. To work in Italian:
  ```json
  { "language": "italian" }
  ```
  Put it in your personal settings, never in a project's `.claude/settings.json`: it would force the language on everyone who opens the project.
- **The app**: the `Language` field of the app's spec, set by the interview to the conversation language. Pages and messages of the app use it, whoever builds or changes it later.

Apps created with earlier, Italian versions of the skills have `scheda.md` instead of `spec.md`. The skills still read them and treat their language as Italian.

## Install

- **Claude Code, as a plugin** (read access to this repo is needed; in the Claude desktop app, type these in the Code tab):
  ```
  /plugin marketplace add citadel-ai-apps/citadel-skills
  /plugin install citadel-skills@citadel-skills
  ```
  To get updates: `/plugin marketplace update citadel-skills`. Then start from `/citadel`.
- **Codex, as a plugin** (same access to the repo):
  ```sh
  codex plugin marketplace add citadel-ai-apps/citadel-skills
  codex plugin add citadel-skills@citadel-skills
  ```
  To get updates: `codex plugin marketplace upgrade`. On Windows, type them in PowerShell.
- **Claude Code, by hand**: link each folder in `skills/` into `~/.claude/skills/`, or into `.claude/skills/` of the project you work in.
- **claude.ai**: zip the skill folder and upload it from Settings → Capabilities → Skills. Only `citadel-interview` works there.

## Tests

```sh
python3 tests/test_scripts.py
node --test 'skills/citadel-new-app/template/test/*.test.mjs'
```

`tests/test_scripts.py` also checks that the skills stay in English and that each one states the language rule.
