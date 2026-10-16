# Citadel skills

Skill per creare app da pubblicare su Citadel, senza la repo di Citadel.

| Skill | Passo |
|---|---|
| `citadel-connect` | collega il computer a Citadel: portale, token, app note |
| `citadel-interview` | dall'idea alla scheda dell'app, con domande semplici |
| `citadel-new-app` | dalla scheda al pacchetto PocketBase, con test e verifica locale |
| `citadel-publish` | dal pacchetto all'app online: caricamento, deploy, stato dei collegamenti |
| `citadel-edit-app` | modifica di un'app esistente: cosa cambiare, scheda, pacchetto, ripubblicazione |

In arrivo: `citadel`, il punto d'ingresso che spiega i passi.

La configurazione comune sta in `~/.config/citadel/config.json` (o nel file indicato da `CITADEL_CONFIG`), gestita da `citadel-connect`.

## Installazione

- **Claude Code**: collega ogni cartella di `skills/` in `~/.claude/skills/`, oppure in `.claude/skills/` del progetto in cui lavori.
- **claude.ai**: comprimi la cartella della skill in uno zip e caricala da Impostazioni → Capacità → Skill. Lì funziona solo `citadel-interview`.
