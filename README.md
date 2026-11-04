# Citadel skills

Skill per creare app da pubblicare su Citadel, senza la repo di Citadel.

| Skill | Passo |
|---|---|
| `citadel` | punto d'ingresso: cosa si può fare e da dove partire |
| `citadel-connect` | collega il computer a Citadel: portale, token, app note |
| `citadel-interview` | dall'idea alla scheda dell'app, con domande semplici |
| `citadel-new-app` | dalla scheda al pacchetto PocketBase, con test e verifica locale |
| `citadel-publish` | dal pacchetto all'app online: caricamento, deploy, stato dei collegamenti |
| `citadel-edit-app` | modifica di un'app esistente: cosa cambiare, scheda, pacchetto, ripubblicazione |

La configurazione è gestita da `citadel-connect`. Ogni progetto può avere il suo ambiente in `.citadel/config.json`, nella radice del repo (escluso da git); se manca vale quella globale, `~/.config/citadel/config.json`. La variabile `CITADEL_CONFIG` le scavalca entrambe.

## Installazione

- **Claude Code, come plugin** (serve l'accesso in lettura a questo repo):
  ```
  /plugin marketplace add Manfrini/citadel-skills
  /plugin install citadel-skills@citadel-skills
  ```
  Per ricevere gli aggiornamenti: `/plugin marketplace update citadel-skills`. Poi parti da `/citadel`.
- **Claude Code, a mano**: collega ogni cartella di `skills/` in `~/.claude/skills/`, oppure in `.claude/skills/` del progetto in cui lavori.
- **claude.ai**: comprimi la cartella della skill in uno zip e caricala da Impostazioni → Capacità → Skill. Lì funziona solo `citadel-interview`.
