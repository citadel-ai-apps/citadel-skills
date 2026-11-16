# Spec template

The spec has two halves. **For the requester** holds the confirmed summary in the user's words and language. **For the builder** turns those answers into choices for Citadel and PocketBase, in English. Every technical choice must trace back to an interview answer or an accepted proposal. A choice without that origin goes under "To decide".

## From answers to choices

**Sign-in**
- Just open the link and browse: `list`/`view` rules open (`""`), `create`/`update`/`delete` closed (`null`).
- Just open the link and fill in a form: `createRule: ""` on the answers collection, reading closed. The owner reads the answers from the `/_/` panel.
- By invitation: `users.createRule = null`. The owner creates users from the `/_/` panel.
- Open sign-up: `users.createRule = ""`. Verifying the email needs an SMTP relay (`smtp_relay`, Tier 2).
- Company account (Google, Microsoft…): `oauth_provider` grant, Tier 2.
- Whenever there are users: behind Citadel's edge, set `trustedProxy` (`X-Forwarded-For`, right-most IP) and the rate limits.

**What each person sees, who changes what**
- Everyone sees only their own entries: a relation field to the user, with the rule `owner = @request.auth.id`.
- Every signed-in user sees everything: `@request.auth.id != ""`.
- A manager sees or approves everything: a role field on the user, with the rule `@request.auth.role = "…"`.

**Content**: each kind of "entry" becomes a collection. The fields come from the concrete example the user gave. Photos and documents become `file` fields, which use the tenant's disk quota. Collection and field names are in English; labels on screen are in the app's language.

**Connections**: each host declared in the package is a **request** for authorisation (a grant): Citadel grants it automatically or passes it to an approver, depending on the tier. Calls start from a server-side hook, never from the browser.

| Situation | Grant | Tier |
|---|---|---|
| Public service at one precise address | `egress_host` (FQDN in `pbapp.json` → `egress`) | 1, automatic |
| Several addresses under a wildcard (`*.example.com`) | `egress_host` | 2, needs an approver |
| Sending email | `smtp_relay` | 2 |
| External file storage | `object_storage` | 2 |
| Custom address (`app.company.com`) | `custom_domain` | 2 |
| Internal system on a private network | none today: private networks are Tier 0 | to decide |

For a service that needs a key, note under "To decide" where to keep it. Citadel does not pass environment variables to the tenant.

**Sensitive data**: if there is personal, health, financial or third-party data, write it in the spec as `Data touched: third-party`. A privacy and security check will be needed before the PR.

**Short name**: at most 10 characters, lowercase letters, digits and hyphens. It becomes the subdomain and the tenant name.

**Language**: the conversation language, written as a language name (`English`, `Italian`…). Pages, messages, empty states and sample data use it.

## Template

Headings and field names stay in English. The "For the requester" section is written in the app's language.

```markdown
# <Title> — spec

- Date: <YYYY-MM-DD>
- Short name: <slug>
- Language: <English | Italian | …>
- Data touched: <none | own | third-party>

## For the requester

<the confirmed summary: What I understood, What you'll see, First version>

## For the builder

### Sign-in
<access model and reason, in one or two lines>

### Data
| Collection | Fields | Who sees | Who creates | Who edits / deletes |
|---|---|---|---|---|

### Connections
| What | What for | Grant | Tier |
|---|---|---|---|
<or: none, so no egress>

### Interface
<main screens, main device>

### Look
- Style: <company | neutral>. Colours: <primary, accent, in hex, or "to collect">. Logo: <file, or "to collect">. Font: <name, or the system one>
- Theme: <follows the computer with a switch | light only | dark only>

## Information to collect
- [ ] <what is needed, for example "address and documentation of the management system's API"> — <who provides it>

## To decide
- <open point> — <proposal, if any>
```

"Information to collect" holds everything needed to build that the interview did not gather. Each connection needs an address, documentation, access type and a contact person. Email needs the sender address and the relay. Company style needs the logo (SVG or PNG) and the colours: who has them, or a company website to take them from. Company sign-in needs the provider and who administers it. Keys are noted only as "who provides it": their value never goes into the spec.

## Older specs

Apps created with earlier versions of the skills have `scheda.md` instead of `spec.md`, with Italian headings (`Nome breve`, `Dati toccati`, `Per chi la costruisce`…). Read them the same way; they have no `Language` field, so their language is Italian. Do not rename the file unless the user asks.
