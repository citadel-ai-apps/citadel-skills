# Modello della scheda

La scheda ha due metà. **Per chi la chiede** riporta il riepilogo confermato con le parole dell'utente. **Per chi la costruisce** traduce quelle risposte in scelte per Citadel e PocketBase. Ogni scelta tecnica deve risalire a una risposta dell'intervista o a una proposta accettata. Una scelta che non ha questa origine va in "Da decidere".

## Dalle risposte alle scelte

**Ingresso**
- Basta aprire il link e si consulta soltanto: regole `list`/`view` aperte (`""`), `create`/`update`/`delete` chiuse (`null`).
- Basta aprire il link e si compila un modulo: `createRule: ""` sulla collezione delle risposte, lettura chiusa. Il proprietario legge le risposte dal pannello `/_/`.
- Su invito: `users.createRule = null`. Il proprietario crea gli utenti dal pannello `/_/`.
- Iscrizione libera: `users.createRule = ""`. Per verificare l'email serve un relay SMTP (`smtp_relay`, Tier 2).
- Account aziendale (Google, Microsoft…): grant `oauth_provider`, Tier 2.
- In ogni caso con utenti: dietro l'edge di Citadel vanno impostati `trustedProxy` (`X-Forwarded-For`, IP più a destra) e i rate limit.

**Cosa vede ognuno, chi cambia cosa**
- Ognuno vede solo le sue voci: un campo relazione all'utente, con regola `utente = @request.auth.id`.
- Tutti gli utenti entrati vedono tutto: `@request.auth.id != ""`.
- Un responsabile vede o approva tutto: un campo ruolo sull'utente, con regola `@request.auth.ruolo = "…"`.

**Contenuto**: ogni tipo di "voce" diventa una collezione. I campi si ricavano dall'esempio concreto che ha dato l'utente. Foto e documenti diventano campi `file`, che occupano la quota disco del tenant.

**Collegamenti**: ogni host dichiarato nel pacchetto è una **richiesta** di autorizzazione (grant): Citadel la concede in automatico o la passa a un approvatore secondo il tier. Le chiamate partono da un hook lato server, mai dal browser.

| Situazione | Grant | Tier |
|---|---|---|
| Servizio pubblico con un indirizzo preciso | `egress_host` (FQDN in `pbapp.json` → `egress`) | 1, automatico |
| Più indirizzi coperti da un jolly (`*.esempio.it`) | `egress_host` | 2, serve un approvatore |
| Invio di email | `smtp_relay` | 2 |
| Archivio file esterno | `object_storage` | 2 |
| Indirizzo proprio (`app.azienda.it`) | `custom_domain` | 2 |
| Sistema interno su rete privata | nessuno oggi: le reti private sono Tier 0 | da decidere |

Per un servizio che vuole una chiave, segna in "Da decidere" dove conservarla. Citadel non passa variabili d'ambiente al tenant.

**Dati delicati**: se ci sono dati personali, sanitari, economici o di terzi, scrivilo nella scheda come `Dati toccati: di terzi`. Prima della PR servirà un controllo di privacy e sicurezza.

**Nome breve**: al massimo 10 caratteri, minuscole, cifre e trattini. Diventa il sottodominio e il nome del tenant.

## Modello

```markdown
# <Titolo> — scheda

- Data: <AAAA-MM-GG>
- Nome breve: <slug>
- Dati toccati: <nessuno | propri | di terzi>

## Per chi la chiede

<il riepilogo confermato: Cosa ho capito, Cosa vedrai, Prima versione>

## Per chi la costruisce

### Ingresso
<modello di accesso e motivo, in una o due righe>

### Dati
| Collezione | Campi | Chi vede | Chi crea | Chi modifica / cancella |
|---|---|---|---|---|

### Collegamenti
| Cosa | A cosa serve | Grant | Tier |
|---|---|---|---|
<oppure: nessuno, quindi niente egress>

### Interfaccia
<schermate principali, dispositivo prevalente, lingua>

## Informazioni da raccogliere
- [ ] <cosa serve, per esempio "indirizzo e documentazione dell'API del gestionale"> — <chi la fornisce>

## Da decidere
- <punto aperto> — <proposta, se c'è>
```

In "Informazioni da raccogliere" va tutto ciò che serve per costruire e che l'intervista non ha raccolto. Per ogni collegamento servono indirizzo, documentazione, tipo di accesso e un referente. Per le email servono l'indirizzo mittente e il relay. Per l'accesso aziendale serve il provider e chi lo amministra. Le chiavi si annotano solo come "chi la fornisce": il loro valore non entra mai nella scheda.
