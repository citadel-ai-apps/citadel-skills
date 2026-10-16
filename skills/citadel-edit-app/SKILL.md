---
name: citadel-edit-app
description: Modifica un'app già esistente su Citadel. Mostra le app disponibili, raccoglie con poche domande cosa cambiare, aggiorna scheda e pacchetto, e ripubblica. Usala quando l'utente vuole cambiare, migliorare, correggere o ampliare un'app Citadel che c'è già.
---

# Modificare un'app Citadel

Tono **asciutto** con l'utente, come nell'intervista: domande discorsive, niente termini tecnici.

## 1. Scegli l'app

`python3 <cartella di citadel-connect>/connect.py apps --dir <cartella di lavoro>` elenca le app note: cartella locale, versione locale, versione online. Mostrale all'utente in una riga ciascuna e chiedi quale modificare. Se la configurazione manca, usa prima `citadel-connect`.

Per modificare un'app serve la sua **cartella di lavoro**, con `scheda.md` e `pkg/`. Citadel non restituisce il codice di un'app pubblicata. Se la cartella non c'è, dillo all'utente e fermati: il codice va recuperato da dove è stato salvato, per esempio un repository git.

Se la versione locale è diversa da quella online, chiedi quale delle due è quella buona prima di andare avanti.

## 2. Cosa cambiare

Leggi `scheda.md`, poi chiedi "Cosa vorresti cambiare?". Fai al massimo tre domande per capire il caso concreto, guidate come in `citadel-interview`: opzioni pronte con lo strumento delle domande a scelta, se c'è. Ogni modifica rientra in uno di questi tipi, e ogni tipo ha la sua conseguenza:

| Tipo | Per esempio | Conseguenza |
|---|---|---|
| Aspetto e testi | colori, parole, ordine dei campi | solo `pb_public/` |
| Nuove informazioni | un campo in più, un nuovo tipo di voce | una **migrazione nuova** |
| Chi vede o cambia cosa | un responsabile, voci condivise | regole in una migrazione nuova |
| Collegamenti | un servizio esterno, invio di email | hook più `egress`; il Tier 2 attende un approvatore |
| Informazioni da togliere | un campo che non serve più | migrazione nuova; **i dati di quel campo si perdono** |

## 3. Riepilogo

```
**Cosa cambia**
- …

**Cosa vedrai di diverso**
<2-4 righe: la passeggiata solo sulle schermate che cambiano>

**Cosa resta uguale**: …
**Attenzione**: … (dati che si perdono, collegamenti da approvare; oppure: niente)
```

Chiedi conferma. Se si perdono dati, serve un sì esplicito su quel punto.

## 4. Costruzione

1. Aggiorna `scheda.md`: le sezioni toccate, più una riga in `## Modifiche` (crea la sezione se manca) con data e versione.
2. Applica la modifica seguendo i passi 3 e 4 di `citadel-new-app`, con le stesse verifiche. In più valgono due regole: le migrazioni già pubblicate restano come sono, e i test esistenti devono restare verdi.
3. Aumenta `version` in `pbapp.json`: il terzo numero per aspetto e correzioni (1.2.0 → 1.2.1), il secondo per tutto il resto (1.2.1 → 1.3.0).

## 5. Pubblicazione

Pubblica con `citadel-publish` e chiudi come indicato lì. Se il deploy fallisce, Citadel ha già rimesso online la versione precedente, dati compresi.
