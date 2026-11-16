# First connection

A tutorial for someone connecting this computer to Citadel for the first time. Five steps, one per message, each headed "Step N of 5". Every step has one line on what it is for, what to do, and a block to copy whenever there is something to type.

**Copy blocks**: you write them, filled in with real values: absolute paths in double quotes, the user's operating system, never a `<placeholder>` left inside. One command per block. On Mac the command is `python3`; on Windows it is `py` (if Windows answers that `py` is not recognised, use `python`; if that fails too, Python is missing: install it as in step 1 of the `citadel` skill).

## Step 1 of 5: what you need

The **token** is your personal key: Citadel uses it to know who is publishing. It is created by the **Citadel operator**, the person who installed Citadel in your company, and it expires (by default after 90 days). From the operator you need four things: the portal address, the apps domain, your token, the short name of your app. A portal password is needed too, later, to manage the app's users once it is online.

If the user does not have them yet, give them this message to send to the operator, translated into their language:

```
Hi, I'd like to build apps on Citadel. Could you send me:
1. the portal address
2. the apps domain
3. a personal token for me
4. the short name of my app (or create one called <app name>)
5. a password to sign in to the portal
Please send the token and the password privately, not in a group chat. Thanks!
```

Then stop: the tutorial resumes when they have the four things. Never ask for the token in the chat.

If the user is the operator, or the operator asks how, the commands run on the Citadel server with the `citadel` command, and the token is printed only once:

```
sudo citadel principal create person:<user> --name "<Full Name>"
sudo citadel principal set-password person:<user> --password "<password>"
sudo citadel tenant create --slug <app> --pb-version 0.42.2 --owner person:<user>
sudo citadel token create --principal person:<user> --name "<user> laptop" --days 90
```

The first three are needed only for a new person and a new app. The password lets the user sign in to the portal, where the app's page has the button that opens its PocketBase admin (`/_/`): that is where they create the app's users and fill in its settings. The short name is at most 10 characters (lowercase letters, digits, hyphens); the PocketBase version must be one the platform offers. Today the portal has no page where users create their own token.

## Step 2 of 5: portal and apps domain

Collect where the configuration applies, the portal and the apps domain with the guided questions in `SKILL.md` (section 2), then run `init` yourself. The user types nothing here.

## Step 3 of 5: open a terminal

The token is typed in a separate window, so it never passes through the chat.

- **Mac**: press `Cmd` + `Space`, type `Terminal`, press `Enter`.
- **Windows**: press the `Windows` key, type `PowerShell`, press `Enter`.

This works the same whether the user is on Claude or on ChatGPT/Codex.

## Step 4 of 5: enter the token

Give the command for their system, ready to paste:

- Mac: `cd "<project folder>"; python3 "<path of connect.py>" set-token`
- Windows: `cd "<project folder>"; py "<path of connect.py>" set-token`

Add `--global` if in step 2 they chose "all projects". Then tell them, in four lines:

1. paste the command in the terminal and press `Enter`;
2. paste the token: `Cmd` + `V` on Mac, `Ctrl` + `V` or right click on Windows. **Nothing appears while you paste: that is normal**;
3. press `Enter`;
4. when the terminal says "Token saved", come back here and write "done".

If the user pastes the token into the chat instead: tell them it is no longer secret, that they must ask the operator to revoke it and send a new one, and repeat this step.

## Step 5 of 5: check

Run `connect.py check --tenant <short name>` yourself and translate the result:

| Result | In plain words | What to do |
|---|---|---|
| `reachable`, `token_valid: true`, app exists | All set | Say so in one line and go back to where the user was |
| portal `unreachable` | Citadel does not answer from here | Check the address; the company network or VPN may be needed |
| `token_valid: false` | Citadel does not recognise the key | Mistyped or expired: repeat step 4, or ask the operator for a new one |
| app `does not exist, or you have no access to it` | The app has not been created yet, or you are not on it | Ask the operator to create it with that short name, or to give you access |

The step is done when all three are green.
