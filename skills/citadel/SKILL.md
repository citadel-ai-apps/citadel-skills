---
name: citadel
description: Punto d'ingresso per Citadel, la piattaforma aziendale che ospita app PocketBase. Spiega cosa si può fare e indirizza alla skill giusta. Usala quando l'utente chiede cos'è Citadel, cosa può fare, come si accede, come si crea, pubblica o modifica un'app, o quando non è chiaro da quale passo partire.
---

# Citadel

Citadel ospita le app interne dell'azienda. Ogni app ha i suoi dati, una pagina web e un indirizzo proprio. Gira isolata dalle altre, e può collegarsi all'esterno solo verso ciò che è stato autorizzato. Chi crea un'app non ha bisogno di sapere programmare: descrive cosa gli serve, e il resto lo fanno le skill.

Tono **asciutto**: rispondi con i passi qui sotto, poi chiedi da dove partire.

## I passi

| Voglio… | Skill | Serve |
|---|---|---|
| collegarmi a Citadel | `citadel-connect` | indirizzo del portale e token, dall'operatore |
| creare un'app nuova | `citadel-interview`, poi `citadel-new-app`, poi `citadel-publish` | un'idea; il nome breve dell'app, creato dall'operatore |
| modificare un'app | `citadel-edit-app` | la cartella di lavoro dell'app |
| ripubblicare un'app | `citadel-publish` | la cartella di lavoro dell'app |

L'intervista si può fare anche senza collegamento a Citadel. Costruzione e pubblicazione richiedono un agente che lavora sul computer, come Claude Code o Codex.

## Chi fa cosa

- **L'utente** descrive l'app, la prova, la pubblica e la modifica.
- **L'operatore di Citadel** crea le app nuove, consegna i token e approva i collegamenti che non sono automatici: un servizio indicato con un jolly, l'invio di email, un indirizzo proprio.
- **Citadel** registra ogni pubblicazione e ogni autorizzazione. Se una pubblicazione fallisce, rimette online da solo la versione precedente.

## Da dove partire

Leggi la configurazione con `python3 <cartella di citadel-connect>/connect.py check`:
- se manca, si parte da `citadel-connect`;
- se c'è, mostra le app note con `connect.py apps` e chiedi se crearne una nuova o modificarne una.
