---
name: citadel-connect
description: Collega questo computer a un'installazione Citadel: indirizzo del portale, token personale, app a cui si ha accesso. Usala quando si deve configurare Citadel, quando un'altra skill Citadel trova la configurazione mancante o il token non valido, o quando l'utente chiede come accedere a Citadel o quali app ha.
---

# Collegarsi a Citadel

Tono **asciutto**: cosa serve, il comando da lanciare, l'esito.

Tutte le skill Citadel leggono la stessa configurazione, gestita da `connect.py` (nella cartella di questa skill). Ogni progetto può avere il suo ambiente:
- **lettura**: vale il `.citadel/config.json` più vicino, dalla cartella corrente fino alla radice del repo git; se non c'è, `~/.config/citadel/config.json` (globale);
- **scrittura**: `init` crea `.citadel/config.json` nella radice del repo (fuori da git, nella cartella corrente) e aggiunge `.citadel/` al `.gitignore`; `set-token` e `add-app` scrivono nel file del progetto e si fermano se manca. Con `--global` tutti e tre usano il file globale;
- la variabile `CITADEL_CONFIG`, se impostata, vale per tutto.

`check` riporta sempre quale file sta usando (`file`, `ambito`).

## 1. Cosa serve

Dall'operatore di Citadel della propria azienda l'utente riceve:
- l'**indirizzo del portale**, per esempio `https://citadel.azienda.it`;
- il **dominio delle app**, per esempio `apps.azienda.it` (in sviluppo può includere lo schema: `http://apps.localhost`);
- un **token personale**;
- il **nome breve** di ogni app su cui può lavorare. Le app nuove le crea l'operatore.

## 2. Configurazione

Lancia i comandi dalla cartella del progetto. Chiedi all'utente se l'ambiente vale solo per questo progetto (predefinito) o per tutti (`--global` in ognuno dei tre comandi).

1. `python3 connect.py init --url <portale> --apps-domain <dominio>`
2. Il token lo inserisce l'utente, digitandolo nascosto. Dagli questo comando da lanciare nel suo terminale, dalla stessa cartella (in Claude Code si lancia dalla chat con `!` davanti; in Codex e altrove, nel terminale):
   `python3 <cartella di questa skill>/connect.py set-token`
   Il token resta fuori dalla chat: se l'utente lo incolla nella conversazione, digli di revocarlo e di chiederne uno nuovo.
3. `python3 connect.py add-app <nome breve>` per ogni app.

## 3. Verifica

`python3 connect.py check --tenant <nome breve>`

Il passo è finito quando il portale risulta raggiungibile, `token_valido` è `true` e ogni app esiste. Altrimenti:
- portale non raggiungibile: l'indirizzo è sbagliato, oppure serve la rete aziendale o la VPN;
- token non valido: va chiesto un token nuovo all'operatore;
- app inesistente: va chiesto all'operatore di crearla.

## 4. Le mie app

Citadel oggi non ha una chiamata che elenca le app di un utente. Le app note sono quindi due insiemi:
- quelle registrate con `add-app`;
- le cartelle di lavoro che contengono `scheda.md` e `pkg/`.

Mostrali insieme: nome breve, cartella locale (se c'è), release online.
