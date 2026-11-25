---
name: citadel-install
description: Installs Citadel for someone who does not have one yet, so they can try it - by default a local trial in a Linux VM on their Mac, on explicit request a pilot on a Linux server. Checks the computer first, asks before installing anything, ends with the portal and a demo app running and writes an install report. Use it when the user has no Citadel in their company, wants to try or install Citadel, or the Citadel wizard reaches "no Citadel yet".
---

# Installing Citadel

**Language**: talk to the user in the user's language (the `language` setting if there is one, otherwise the language they write in). Commands, file names and README section names stay in English. The report is written in the user's language.

**Tone: terse and childproof.** The user may never have opened a terminal. You do the work; the user chooses and approves.

Citadel's source is at https://github.com/citadel-ai-apps/citadel. Its `README.md` is the source of truth for the commands: **read it at run time** and follow it. The steps below say which sections to follow and in what order, not every command, so the skill keeps working when the README changes. If the README contradicts this skill on a command, follow the README and note it in the report.

## Rules

- **Check before acting.** Step 1 runs before anything is installed or cloned.
- **Ask before installing any software** (Homebrew packages, UTM, Go, anything with `brew`, `apt`, `winget` or an installer). One question listing everything missing, with what each piece is for in a few words. Cloning the repo and building inside its folder need no extra permission once the user has agreed to the install.
- **One plain sentence before each step**: what it does and roughly how long it takes, then run it. Long commands (VM creation, provisioning, image builds) run in the background; tell the user they can wait and that you will say when it is done.
- **Never disable a security control to make a step pass**: gVisor (`runsc`), user-namespace remapping, firewall rules and the firewall backend, image digests (no `allow_unpinned_images`, no tags in place of digests), the portal's localhost binding outside the dev VM. If a step only passes without one of them, it has failed.
- **Two failed attempts on the same step: stop.** Tell the user what failed, the last lines of the error, what you tried, and that the report has the details for the Citadel team. Do not try a third workaround.
- **Never ask for a password or token in the chat.** Passwords Citadel needs for the trial are generated on the user's computer and shown to the user, never pasted into an external service.
- **Time every step** (start and end time) and note every error and every question to the user: they go in the report (step 6).

## 1. Check the computer

Find out yourself, with commands:

- **System and architecture**: `uname -sm` (Mac: `sw_vers`; Windows: PowerShell `$PSVersionTable`, `[Environment]::Is64BitOperatingSystem`).
- **Free disk** in the home folder: `df -h ~`. The VM disk grows up to 64 GiB (`PB_VM_DISK_GIB` in `hack/vm/README.md`); ask for at least **40 GB** free to start. Below that, say so and stop.
- **Memory**: `sysctl hw.memsize` on Mac, `free -g` on Linux. The VM takes 8 GiB (`PB_VM_MEM_MIB`): under 16 GB on the host, warn that the Mac will be slow while it runs.
- **Prerequisites** listed in the README's "Running it locally" section (today: Go at the version in `go.mod`, `make`, `python3`, `git`, UTM, `ast-grep`, `shellcheck`): check each one (`command -v`, `go version`, `ls /Applications/UTM.app`) and Homebrew (`brew --version`), which installs the others on a Mac.

Show the result as a short table: what is there, what is missing, what each missing piece is for. Then:

| System | What to do |
|---|---|
| Mac (Apple Silicon or Intel) | local trial (step 2) |
| Linux, and the user explicitly asked for a server | server pilot (step 3) |
| Linux desktop, no request for a server | explain the local trial needs a Mac with UTM; offer the server path (step 3) on this machine if it is a disposable VM, with its warning |
| Windows, or anything else | say at once that Citadel does not run there: it needs Linux kernel features (gVisor, netfilter, user namespaces). Closest options: a Mac, or a Linux VM or server the user controls (step 3). Do not attempt WSL or Docker Desktop workarounds |

Ask permission for the missing software in one question, install it, check again. Done when every prerequisite answers.

## 2. Local trial (default)

The README's **"Running it locally"** section: a UTM VM on the Mac, driven from the repo.

1. **Get the source.** Clone into the work folder (suggest `~/Documents/citadel`; if it exists, `git pull` instead). If the clone is refused, the user has no access to the repo: tell them to ask the Citadel team for it and stop.
2. **Read** `README.md` ("Running it locally", "First run", "The short way") and `hack/vm/README.md`.
3. **First run**, one command at a time, in the order the README gives them (today: `make vm-create`, `make vm-up`, `make vm-provision`, `make vm-bootstrap`, `make images-all`). Before each, one sentence; for example: "`vm-bootstrap` turns on user-namespace remapping and rebuilds the image store: it is the slow one, 10-20 minutes". UTM may ask the user to confirm something on screen: tell them what to click.
4. **The short way**: `make accept-packages ARGS=--keep`. It runs the package suite and leaves the control plane and a demo app running, then prints the portal URL with its sign-in, the daemon's pid and the app URL. Keep that output: it has what step 4 needs.

Done when the printed portal URL answers in a browser (`curl -fsS <portal>` from the Mac) and the app URL answers `/api/health`.

## 3. Server pilot (only on explicit request)

Only when the user asks for it in words ("on a server", "on our Linux VM"). Before starting, say plainly:

> This gives you a **pilot**, not a production install. Citadel does not yet set up autostart (systemd units), a firewall that survives a reboot, wildcard TLS certificates or off-site backups. After a reboot it has to be started again by hand, and it should not hold data you cannot lose.

Then follow the README's **"Deploying to a running VM"** section (host prepared with the provisioning and bootstrap scripts, images built, config written, control plane started as root, network probes and red-team matrix run before any traffic). Where it points to "Starting the control plane" and "Provisioning a tenant", follow those. The red-team matrix is part of the install, not optional: if a probe reaches its goal, stop and report. Ask for the host's address and how you reach it (ssh); never ask for its password in the chat.

Done when `citadel fleet` answers on the host and a demo tenant answers `/api/health`.

## 4. What the user gets

Tell the user, in a few lines, with the real values:

- **Portal**: its address (local trial: `http://<VM_IP>:8080/`) and how to sign in: the principal and password printed by step 2.4, or the ones set with `citadel principal set-password` (README "The tenant portal"). Tell them to keep the password somewhere safe.
- **Demo app**: its address (local trial: `http://<slug>.apps.<VM_IP>.nip.io/`) and its admin at `/_/`, opened from the portal with **Open PocketBase admin**. If the name does not resolve (some routers block nip.io), say so and add it to `/etc/hosts` with the user's permission.
- **Stop everything**: `hack/in-vm.sh pkill -f controlplaned` stops the control plane; `make vm-down` shuts the VM. Nothing is lost.
- **Start again**: `make vm-up`, then start the control plane as in the README's "Starting the control plane" (or run "The short way" again). `make vm-status` says whether the VM is healthy. Give the exact commands for this computer, as copy blocks, run from the Citadel folder.
- **Remove it all**, if asked: the README's teardown (`citadel tenant destroy`, `pkill -f controlplaned`), `make vm-down`, then delete the stopped VM in UTM. Warn: never delete a running VM, or a duplicate `citadel` entry, from UTM's window (`hack/vm/README.md`, "Duplicate VM entries"); `make vm-doctor` checks for duplicates first.

## 5. Connect and build

1. **Token**: the user creates their own token on the VM (README "The tenant portal": `hack/in-vm.sh bin/citadel token create --principal <the principal> --name skills`). It prints the secret once: the user runs it **in a terminal window of their own**, not in the chat's shell, and keeps the window open for the next step. Give the exact command as a copy block.
2. **Connect**: run `citadel-connect` against the new portal. The values are already known, so its questions are a confirmation: portal `http://<VM_IP>:8080`, apps domain `http://apps.<VM_IP>.nip.io`, app `demo` (or the slug printed in step 2.4). The user types the token hidden with `connect.py set-token`, as `citadel-connect` explains.
3. **Offer the first app**: "Citadel is running. Do you want to build your first app now?" If yes, continue with the `citadel` wizard from step 4 (the interview). On this local Citadel the user is also the operator: new apps are created with `citadel tenant create` (README "Provisioning a tenant"), which you run for them when `citadel-publish` needs an app that does not exist.

## 6. Install report

Write `citadel-install-report.md` in the work folder the user started from, in the user's language, also when the install stopped early. Contents:

- date, system and version, CPU architecture, memory, free disk at the start;
- path taken (local trial or server pilot) and total time;
- a table of steps: command, start, duration, result;
- each error: the step, the key lines of the message, what fixed it (or "not solved");
- what needed the user's input (permissions, clicks in UTM, passwords) and how long they waited;
- what was unclear, wrong or missing in the README, with the section name;
- the Citadel commit installed (`git rev-parse --short HEAD`).

No passwords, tokens or other secrets in the report. Tell the user where it is and that they may send it to the Citadel team: it is how the install gets easier for the next person.
