---
name: citadel-publish
description: Pubblica su Citadel un'app già costruita. Carica il pacchetto, fa il deploy, restituisce l'indirizzo e lo stato dei collegamenti esterni. Usala quando un'app per Citadel va pubblicata, messa online, aggiornata o rilasciata.
---

# Pubblicare un'app su Citadel

Tono **asciutto** con l'utente: esito, indirizzo, cosa resta da fare.

## 1. Configurazione

Servono tre dati: l'indirizzo del portale Citadel (`url`), un token personale (`token`), il dominio delle app (`apps_domain`, per esempio `apps.azienda.it`; in sviluppo può includere lo schema, `http://apps.localhost`). Lo script li legge dalle variabili `CITADEL_URL`, `CITADEL_TOKEN` e `CITADEL_APPS_DOMAIN`, oppure da `~/.config/citadel/config.json`.

Se mancano, chiedi all'utente indirizzo e dominio. Il **token lo salva l'utente**: lo riceve dall'operatore di Citadel, e tu gli dai il comando per scriverlo nel file con permessi 600. Il valore del token resta fuori dalla chat e da ogni output.

## 2. Pacchetto e app

- **App di destinazione**: il "Nome breve" della scheda (`<nome>/scheda.md`). La crea l'operatore di Citadel: se l'API risponde 404 sull'app, dillo all'utente e fermati.
- **Versione**: aumenta `version` in `pbapp.json` rispetto all'ultima pubblicata.
- **Controllo**: `python3 <cartella di citadel-new-app>/check_package.py <nome>/pkg` deve rispondere `ok`.

## 3. Pubblicazione

```sh
python3 <cartella di questa skill>/publish.py <nome>/pkg --tenant <nome breve>
```

Lo script crea uno zip riproducibile, lo carica, avvia il deploy e legge lo stato dei collegamenti. Restituisce un JSON ed esce con 0 solo se il deploy è riuscito. Con `--dry-run` mostra il contenuto dello zip senza caricare nulla.

Il deploy di Citadel segue questa sequenza: salvataggio dei dati, sostituzione della versione, controllo di salute, richieste `smoke`. Se un passo fallisce, Citadel torna da solo alla versione precedente, codice e dati (`tornato_indietro: true`).

## 4. Esito

Un messaggio breve all'utente:

- **Riuscito**: l'indirizzo dell'app e come si entra, secondo la sezione Ingresso della scheda. Per esempio: "gli utenti li crei dal pannello `/_/`", oppure "basta aprire il link".
- **Collegamenti**: per ogni host, autorizzato oppure in attesa. Un host in attesa (Tier 2) va approvato dall'operatore nel portale, alla pagina delle autorizzazioni; fino ad allora le chiamate verso quell'host falliscono e l'app deve mostrare un messaggio chiaro.
- **Fallito**: in quale passo (`passo_fallito`), il motivo detto in parole semplici, e che è ancora online la versione precedente. Poi correggi con `citadel-new-app` partendo dall'`errore` e dal `log`, e ripubblica.
