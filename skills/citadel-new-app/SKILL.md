---
name: citadel-new-app
description: Costruisce un'app nuova per Citadel partendo dalla sua scheda. Produce il pacchetto PocketBase (migrazioni, hook, pagine) con i test, e lo verifica in locale. Usala quando c'è da creare o costruire un'app per Citadel, o quando una scheda in `<nome>/scheda.md` è pronta per essere costruita.
---

# Costruire un'app per Citadel

Citadel ospita app PocketBase. Ogni app è un **pacchetto**: migrazioni per i dati, hook per la logica lato server, pagine statiche, un manifest. La piattaforma ci mette il resto (binario, rete, backup). Il pacchetto si scrive in qualsiasi cartella: non serve la repo di Citadel.

Tono **asciutto** con l'utente: frasi brevi, elenchi, dettagli tecnici solo se li chiede.

## Cartella dell'app

```
<nome>/
  scheda.md      cosa fare e perché (da citadel-interview)
  pkg/           il pacchetto: pbapp.json, pb_migrations/, pb_hooks/, pb_public/
  test/          *.test.mjs, lanciati con node --test
```

## 1. Scheda

Leggi `<nome>/scheda.md`. Se la scheda manca, fai prima l'intervista con `citadel-interview`.

Poi passa le due liste in fondo alla scheda:
- **Informazioni da raccogliere**: chiedi all'utente quelle che servono per costruire adesso, una per messaggio. Un dato che nessuno ha (per esempio la documentazione di un'API) diventa uno stub ben segnalato nel codice e una voce della chiusura.
- **Da decidere**: ogni punto che cambia il codice va chiuso ora. Proponi una scelta in una riga e chiedi conferma.

Ogni decisione presa qui va scritta nella scheda, nella sezione che riguarda.

## 2. Piano

Mostra il piano in non più di otto righe: collezioni, schermate, collegamenti, file che creerai. Chiedi "procedo?" e attendi il sì.

## 3. Costruzione

Parti da [template/](template/): copia `pkg/` e `test/` nella cartella dell'app, sostituisci `NOME` e crea `pb_migrations/` e `pb_hooks/` quando servono. Poi, in quest'ordine:

1. **Migrazioni**: una collezione per ogni riga della tabella Dati della scheda, con regole che riproducono esattamente le colonne "chi vede / chi crea / chi modifica". Ogni regola deve risalire alla scheda.
2. **Hook**: solo per i collegamenti esterni e per la logica che il browser non deve vedere.
3. **Pagine**: le schermate della sezione Interfaccia, con le parole della scheda, e lo stile della sezione Aspetto (vedi [pocketbase.md](pocketbase.md#aspetto)).
4. **Manifest**: `name`, `version`, `egress` (un host per ogni collegamento), le richieste `smoke`.

Prima di scrivere migrazioni o hook leggi [pocketbase.md](pocketbase.md): la sintassi corretta, gli schemi già collaudati su Citadel e gli errori più comuni. Le regole del formato del pacchetto sono in [package.md](package.md).

## 4. Verifica

Il passo è finito quando tutte e tre le verifiche passano:

1. `node --test '<nome>/test/*.test.mjs'` è verde.
2. `python3 <cartella di questa skill>/check_package.py <nome>/pkg` risponde `ok`.
3. **Prova in locale**, se `pocketbase` è installato: avvialo sul pacchetto (comando in [pocketbase.md](pocketbase.md#prova-in-locale)). Ogni richiesta `smoke` del manifest deve rispondere con il suo `expectStatus`. Se `pocketbase` non c'è, chiedi all'utente se scaricarlo; se dice no, segna la prova come non fatta.

Correggi e ripeti finché non passano.

## 5. Chiusura

Un messaggio breve:
- cosa hai costruito: collezioni, schermate, collegamenti;
- come provarla in locale, se l'hai avviata;
- cosa manca: stub, informazioni non arrivate, prove non fatte;
- il passo successivo: pubblicarla su Citadel con `citadel-publish`.
