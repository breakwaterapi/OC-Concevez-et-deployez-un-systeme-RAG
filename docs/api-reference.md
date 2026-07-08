# Référence API

Documentation interactive complète (schémas, exemples, essai en direct) sur
[http://localhost:8001/docs](http://localhost:8001/docs) une fois l'API démarrée. Cette page donne
un tour rapide via `curl`.

## `POST /ask`

Poser une question sur les événements indexés.

```bash
curl -s -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quels concerts sont prévus en Île-de-France ce mois-ci ?"}' | jq
```

Réponses d'erreur : `400` (question vide), `503` (index non construit — appeler `/rebuild`).

## `GET /health`

État de santé de l'API et de ses dépendances (Faiss, Mistral). Toujours `200` — le statut se lit
dans le corps (`"status": "ok"`).

```bash
curl -s http://localhost:8001/health | jq
```

## `GET /metadata`

Métadonnées du corpus actuellement indexé (région, période, tailles, modèles).

```bash
curl -s http://localhost:8001/metadata | jq
```

## `GET /documents`

Liste paginée des documents indexés.

```bash
curl -s "http://localhost:8001/documents?limit=10&offset=0" | jq
```

## `GET /documents/{uid}`

Un document par son identifiant. `404` si absent.

```bash
curl -s http://localhost:8001/documents/<uid> | jq
```

## `GET /retrieve`

Recherche sémantique brute (sans génération) — inspecter ce que `/ask` utiliserait comme contexte.

```bash
curl -s "http://localhost:8001/retrieve?q=concert%20jazz&k=5" | jq
```

## `POST /rebuild`

Reconstruit l'index vectoriel depuis Open Agenda. Protégé par une clé API (`X-API-Key`, valeur de
`REBUILD_API_KEY` dans `.env`). Coûteux (appels réels OpenAgenda + Mistral) — préférer `make up`
pour le seeding initial (voir [Démarrage](getting-started.md)), cette route sert plutôt à
rafraîchir une instance déjà démarrée.

```bash
curl -s -X POST http://localhost:8001/rebuild -H "X-API-Key: $REBUILD_API_KEY" | jq
```
