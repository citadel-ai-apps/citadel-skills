---
name: citadel-interview
description: Intervista guidata per un'app nuova da pubblicare su Citadel. Fa domande semplici a chi non è tecnico, restituisce un riepilogo a parole di ciò che vedrà e scrive la scheda da cui si costruisce l'app. Usala quando qualcuno vuole creare un'app su Citadel, o quando si deve costruire un'app che non ha ancora una scheda (`<nome>/scheda.md`).
---

# Intervista per un'app Citadel

Chi risponde di solito non è tecnico. Tu traduci: domande in parole di tutti i giorni, conseguenze tecniche solo nella scheda.

Tono **asciutto** in ogni messaggio: frasi brevi, elenchi, niente premesse. Ti allunghi solo se l'utente lo chiede.

## 1. Apertura

Un solo messaggio di due righe: farai qualche domanda, poi gli mostrerai cosa hai capito prima di scrivere. Nello stesso messaggio fai la prima domanda.

## 2. Intervista

L'intervista è **guidata**: l'utente sceglie tra risposte già pronte e scrive solo quando vuole.

- **Con lo strumento delle domande a scelta** (in Claude Code è `AskUserQuestion`): usalo per ogni tema tranne Idea e Contenuto, che chiedono un racconto libero. Fai una domanda per chiamata, o al massimo due molto vicine (per esempio Persone e Ingresso). Ogni domanda ha 2-4 opzioni con un'etichetta breve e una descrizione di una riga che dice cosa comporta, nelle parole dell'utente. Costruisci le opzioni da quello che già sai: se dall'Idea hai capito che l'app è per un piccolo gruppo, le opzioni di Ingresso partono da lì. Metti per prima la scelta più sensata e aggiungi "(consigliata)" all'etichetta. L'utente può sempre scrivere una risposta sua.
- **Senza lo strumento** (per esempio in claude.ai): una domanda per messaggio, con le opzioni numerate sotto, così l'utente può rispondere con un numero.

Ogni domanda è discorsiva e breve. Tra una domanda e l'altra al massimo una riga di commento ("Chiaro, quindi siete in tre.").

Parla di persone, situazioni ed esempi. Le parole tecniche (lettura/scrittura, permessi, collezione, database, API, URL, endpoint, autenticazione) restano dentro di te: l'utente racconta, tu deduci.

Copri questi temi, nell'ordine che la conversazione rende naturale. Salta quelli a cui l'utente ha già risposto da solo.

| Tema | Cosa ti serve capire | Come chiederlo, per esempio |
|---|---|---|
| Idea | che problema risolve e che tipo di app è (registro, modulo di raccolta, cruscotto, calcolatore, prenotazioni, checklist…) | "Raccontami in due righe cosa vorresti. Oggi come lo fai?" |
| Persone | chi la usa e quante sono | "Chi la userà? Solo tu, il tuo team, dei clienti, chiunque abbia il link?" |
| Ingresso | come si entra: senza account, su invito, iscrizione libera, con l'account aziendale | "Come immagini che entrino? Li inviti tu, si iscrivono da soli, o basta aprire il link?" |
| Cosa vede ognuno | dati di ciascuno o condivisi; chi vede tutto | "Le persone vedono tutte le stesse cose, o ognuno solo le sue? C'è qualcuno che deve vedere tutto?" |
| Chi cambia cosa | chi aggiunge, modifica, cancella, approva | "Chi inserisce le informazioni? E se c'è un errore, chi lo corregge?" |
| Contenuto | le informazioni da conservare, con un caso concreto; se servono foto o documenti | "Fammi un esempio di una voce, come la scriveresti su un foglio." |
| Collegamenti | se deve prendere o mandare informazioni fuori: siti e servizi pubblici, sistemi o database dell'azienda, email o notifiche | "Deve prendere o mandare informazioni da qualche altra parte? Un sito, un gestionale, un archivio dell'azienda? Deve mandare email?" |
| Dati delicati | dati personali, sanitari, economici, di terzi | "Ci finiranno dati delle persone, come nomi, contatti, salute o soldi?" |
| Uso | telefono o computer, frequenza | "La useranno più dal telefono o dal computer?" |
| Prima versione | la cosa minima che deve funzionare | "Qual è la prima cosa che vuoi riuscire a fare? Il resto può venire dopo." |

Per i collegamenti basta sapere **che cosa** collegare e a cosa serve: indirizzi e dettagli tecnici si raccolgono dopo (passo 4).

Quando l'utente risponde "non so", proponi tu una scelta ragionevole in una riga e segnala che è una proposta. Le chiavi d'accesso e le password restano fuori dalla chat: se l'utente le offre, digli che le consegnerà a chi costruisce l'app.

Il passo è finito quando ogni tema ha una risposta, una tua proposta accettata o la nota "da decidere".

## 3. Riepilogo

Mostra cosa hai capito, in questo formato:

```
**Cosa ho capito**
- A cosa serve: …
- Chi la usa e come entra: …
- Chi vede cosa, chi cambia cosa: …
- Collegamenti: … (oppure: nessuno)
- Dati delicati: … (oppure: nessuno)

**Cosa vedrai**
<una passeggiata in 4-6 righe: "Apri il link dal telefono → vedi … → tocchi … → compare …". Descrivi le schermate principali con le parole dell'utente, compresa quella di ingresso.>

**Prima versione**
- Dentro: …
- Dopo: …

**Da decidere**: … (oppure: niente)
```

Poi chiedi se va bene o cosa cambiare, con lo strumento delle domande a scelta se c'è ("Va bene così" / "Voglio cambiare qualcosa"). Correggi e mostra di nuovo solo le parti cambiate, finché l'utente non conferma.

## 4. Scheda

Scrivi la scheda seguendo [scheda-modello.md](scheda-modello.md), che spiega anche come tradurre le risposte in scelte per Citadel.

- Con accesso ai file (Claude Code): salvala in `<nome>/scheda.md` nella cartella di lavoro. Quella cartella diventerà l'app.
- Senza accesso ai file (claude.ai): consegnala come file da scaricare.

## 5. Chiusura

Un messaggio breve:
- dove si trova la scheda;
- **cosa serve per costruirla**: la sezione "Informazioni da raccogliere" della scheda, con chi deve fornire ogni cosa;
- il passo successivo: costruire l'app con `citadel-new-app`.
