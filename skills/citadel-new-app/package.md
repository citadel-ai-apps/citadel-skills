# Il pacchetto Citadel

## Contenuto

Uno zip che contiene **solo**:

```
pbapp.json       manifest
pb_migrations/   *.js     schema dei dati, applicato al deploy
pb_hooks/        *.js     logica lato server (*.pb.js caricati da soli, gli altri via require)
pb_public/       qualsiasi file statico, servito alla radice del sito
```

Citadel rifiuta il caricamento, indicando il percorso che non va, quando:
- c'è un file fuori da queste quattro voci;
- in `pb_migrations/` o `pb_hooks/` c'è un file che non è `.js`;
- un file è un link simbolico, ha il bit eseguibile o setuid, oppure è un percorso assoluto o contiene `..`;
- si superano 50 MiB non compressi o 2000 file, oppure la compressione è sospetta (rapporto oltre 200);
- il manifest non è valido (vedi sotto).

`check_package.py` controlla tutto questo in locale.

## Manifest (`pbapp.json`)

```json
{
  "schemaVersion": 1,
  "name": "prenota-sale",
  "version": "1.0.0",
  "pocketbase": { "min": "0.38.0", "max": "0.40.x" },
  "egress": ["api.esempio.it"],
  "healthcheck": { "path": "/api/health", "expectStatus": 200 },
  "smoke": [
    { "method": "GET", "path": "/", "expectStatus": 200 }
  ]
}
```

- `schemaVersion`: sempre `1`.
- `name`, `version`: testo, al massimo 64 caratteri. Aumenta `version` a ogni pubblicazione.
- `pocketbase`: l'intervallo di versioni compatibili. `x` è ammesso solo dopo la versione principale (`0.40.x`). Deve contenere almeno una versione offerta dalla piattaforma: oggi `0.38.2` e `0.40.4`.
- `egress`: gli host esterni che l'app chiamerà dal server. È una **richiesta**: un host preciso viene autorizzato in automatico, un jolly (`*.esempio.it`) attende un approvatore. Sono rifiutati indirizzi IP, jolly sul dominio di primo livello, reti private, domini della piattaforma. Vuoto o assente vuol dire nessuna uscita verso internet.
- `healthcheck`: predefinito `GET /api/health` → 200.
- `smoke`: richieste ripetute dopo ogni deploy. Se una fallisce, Citadel torna alla versione precedente, codice e dati. Metti una richiesta per ogni pagina e file JS principale, e una per ogni rotta degli hook, anche su un caso d'errore atteso (per esempio un parametro non valido → 400).

## Ambiente di esecuzione

- **Nessuna variabile d'ambiente** per l'app: le chiavi d'accesso vanno conservate come descritto in [pocketbase.md](pocketbase.md#chiavi-daccesso).
- **Rete**: solo gli host di `egress` già autorizzati. Una chiamata a un host in attesa di approvazione fallisce, e il portale ne mostra il motivo.
- **Filesystem in sola lettura**, tranne i dati di PocketBase. Niente shell: `$os.exec` e simili non funzionano.
- **Disco** con quota per app: i campi `file` la consumano.
- L'app risponde su `https://<nome breve>.<dominio delle app>`, dietro un proxy di Citadel.
