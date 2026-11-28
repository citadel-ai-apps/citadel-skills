# First connection

A tutorial for someone connecting this computer to Citadel for the first time. Five steps, one per message, each headed "Step N of 5". Every step has one line on what it is for, what to do, and a block to copy whenever there is something to type.

**Copy blocks**: you write them, filled in with real values: absolute paths in double quotes, the user's operating system, never a `<placeholder>` left inside. One command per block. On Mac the command is `python3`; on Windows it is `py` (if Windows answers that `py` is not recognised, use `python`; if that fails too, Python is missing: install it as in step 1 of the `citadel` skill).

## Step 1 of 5: what you need

The **token** is your personal key: Citadel uses it to know who is publishing. You create it yourself on the Citadel portal, in step 4, and it expires (by default after 90 days). First you need four things from the **Citadel operator**, the person who installed Citadel in your company: the portal address, the apps domain, the short name of your app, and a password to sign in to the portal. The same password later opens the app's admin, to manage its users once it is online.

If the user does not have them yet, give them this message to send to the operator, translated into their language:

```
Hi, I'd like to build apps on Citadel. Could you send me:
1. the portal address
2. the apps domain
3. the short name of my app (or create one called <app name>)
4. a password to sign in to the portal
Please send the password privately, not in a group chat. Thanks!
```

Then stop: the tutorial resumes when they have the four things. Never ask for the password or the token in the chat.

If the user is the operator, or the operator asks how, the commands run on the Citadel server with the `citadel` command:

```
sudo citadel principal create person:<user> --name "<Full Name>"
sudo citadel principal set-password person:<user> --password "<password>"
sudo citadel tenant create --slug <app> --pb-version 0.42.2 --owner person:<user>
```

They are needed only for a new person and a new app. The password lets the user sign in to the portal, where the app's page has the button that opens its PocketBase admin (`/_/`): that is where they create the app's users and fill in its settings. The short name is at most 10 characters (lowercase letters, digits, hyphens); the PocketBase version must be one the platform offers. The operator does not create the user's token: the user does, on the portal. `citadel token create` stays for service accounts, such as a CI pipeline.

## Step 2 of 5: portal and apps domain

Collect where the configuration applies, the portal and the apps domain with the guided questions in `SKILL.md` (section 2), then run `init` yourself. The user types nothing here.

## Step 3 of 5: open a terminal

The token is typed in a separate window, so it never passes through the chat.

- **Mac**: press `Cmd` + `Space`, type `Terminal`, press `Enter`.
- **Windows**: press the `Windows` key, type `PowerShell`, press `Enter`.

This works the same whether the user is on Claude or on ChatGPT/Codex.

## Step 4 of 5: create and enter the token

First the token. Tell them, in four lines, with the real portal address:

1. open `<portal address>/tokens` in the browser and sign in with the portal password;
2. under "Create a token", write a name for this computer (for example "<first name> laptop") and leave the lifetime as it is;
3. press **Create token**, then **copy**. The token is shown only once: keep the page open until the terminal says "Token saved";
4. come back here.

Then give the command for their system, ready to paste:

- Mac: `cd "<project folder>"; python3 "<path of connect.py>" set-token`
- Windows: `cd "<project folder>"; py "<path of connect.py>" set-token`

Add `--global` if in step 2 they chose "all projects". Then tell them, in four lines:

1. paste the command in the terminal and press `Enter`;
2. paste the token: `Cmd` + `V` on Mac, `Ctrl` + `V` or right click on Windows. **Nothing appears while you paste: that is normal**;
3. press `Enter`;
4. when the terminal says "Token saved", come back here and write "done".

If the user pastes the token into the chat instead: tell them it is no longer secret, that they must press **revoke** next to it on the portal's tokens page and create a new one, and repeat this step. The same if the page was closed before the token was saved: create a new one, and revoke the lost one.

## Step 5 of 5: check

Run `connect.py check --tenant <short name>` yourself and translate the result:

| Result | In plain words | What to do |
|---|---|---|
| `reachable`, `token_valid: true`, app exists | All set | Say so in one line and go back to where the user was |
| portal `unreachable` | Citadel does not answer from here | Check the address; the company network or VPN may be needed |
| `token_valid: false` | Citadel does not recognise the key | Mistyped, expired or revoked: create a new one at `<portal address>/tokens` and repeat step 4 |
| app `does not exist, or you have no access to it` | The app has not been created yet, or you are not on it | Ask the operator to create it with that short name, or to give you access |

The step is done when all three are green.
