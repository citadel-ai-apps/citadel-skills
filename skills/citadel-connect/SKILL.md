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

Parti da `python3 connect.py check` lanciato nella cartella del progetto. Se la configurazione manca, il portale non risponde o un dato è sbagliato, raccogli i dati con domande guidate, non con una richiesta in prosa.

### Domande

- **Con lo strumento delle domande a scelta** (in Claude Code è `AskUserQuestion`; altri agenti possono averne uno equivalente): al massimo due domande per chiamata, 2-4 opzioni ciascuna con un'etichetta breve e una riga che dice cosa comporta. Metti per prima la scelta più sensata con "(consigliata)". L'utente può sempre scrivere una risposta sua: ricordaglielo quando nessuna opzione può essere quella giusta (un indirizzo che non conosci).
- **Senza lo strumento**: una domanda per messaggio, opzioni numerate sotto, e "oppure scrivilo".

Costruisci le opzioni da quello che sai già: il risultato di `check` (anche una configurazione globale vecchia), le app trovate da `connect.py apps`, quello che l'utente ha detto. Se un valore noto non funziona, mostralo comunque con la nota del problema ("risponde 401", "non raggiungibile"), così l'utente lo riconosce.

Chiedi solo ciò che manca o non va, in quest'ordine:

1. **Dove vale** (e **portale**, nella stessa chiamata):
   - "Solo questo progetto (consigliata)": il file `.citadel/config.json` del progetto;
   - "Tutti i progetti": quello globale, con `--global` in ognuno dei comandi sotto.
   Per il portale: l'indirizzo noto, se c'è, più "Lo scrivo io" con un esempio (`https://citadel.azienda.it`).
2. **Dominio delle app** (e **app**, nella stessa chiamata):
   - per il dominio proponi quello che si ricava dal portale: lo stesso host (`citadel.azienda.it`, le app sono `<nome>.citadel.azienda.it`) oppure `apps.` davanti; più quello già noto, se diverso;
   - per le app, a scelta multipla: i nomi brevi noti, più "Un altro: lo scrivo". Il nome breve lo dà l'operatore, al massimo 10 caratteri.
3. **Token**: mai come domanda. È un segreto e non deve passare nella chat: vedi il passo 2 sotto.

Prima di scrivere riassumi in una riga (dove vale, portale, dominio, app) e procedi.

### Comandi

1. `python3 connect.py init --url <portale> --apps-domain <dominio>`
2. Il token lo inserisce l'utente, digitandolo nascosto. Dagli questo comando da lanciare nel suo terminale, dalla stessa cartella (in Claude Code si lancia dalla chat con `!` davanti; in Codex e altrove, nel terminale):
   `python3 <cartella di questa skill>/connect.py set-token`
   Il token resta fuori dalla chat: se l'utente lo incolla nella conversazione, digli di revocarlo e di chiederne uno nuovo.
3. `python3 connect.py add-app <nome breve>` per ogni app.

## 3. Verifica

`python3 connect.py check --tenant <nome breve>`

Il passo è finito quando il portale risulta raggiungibile, `token_valido` è `true` e ogni app esiste. Altrimenti torna alle domande solo per il dato che non va:
- portale non raggiungibile: l'indirizzo è sbagliato, oppure serve la rete aziendale o la VPN;
- token non valido: va chiesto un token nuovo all'operatore;
- app inesistente: va chiesto all'operatore di crearla.

## 4. Le mie app

Citadel oggi non ha una chiamata che elenca le app di un utente. Le app note sono quindi due insiemi:
- quelle registrate con `add-app`;
- le cartelle di lavoro che contengono `scheda.md` e `pkg/`.

Mostrali insieme: nome breve, cartella locale (se c'è), release online.
