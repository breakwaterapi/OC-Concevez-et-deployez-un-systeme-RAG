# Démarrage

## Prérequis

- **Docker** + **Docker Compose** (seule dépendance pour `make up` — pas besoin de Python/uv en local).
- Une clé API [Mistral](https://console.mistral.ai/) valide.
- `make` (préinstallé sur macOS/Linux ; sur Windows, utiliser WSL).

## Configuration

```bash
cp .env.example .env
```

Renseigner au minimum `MISTRAL_API_KEY` dans `.env`. `REBUILD_API_KEY` protège l'endpoint
`POST /rebuild` — changez la valeur par défaut si vous exposez l'API au-delà de `localhost`.
`OPENAGENDA_MAX_RECORDS` contrôle la taille du corpus indexé (1 000 par défaut, 10 000 maximum à cause de la limite d'offset de l'API OpenAgenda).

## Lancer le projet

```bash
make up
```

Cette commande, dans l'ordre :

1. Construit les images Docker (`docker compose build`).
2. Si `models/faiss_index/index.faiss` est absent, lance un conteneur éphémère qui exécute
   `scripts/build_index.py` : récupération des événements Open Agenda, nettoyage, découpage en
   chunks, calcul des embeddings Mistral (barre de progression affichée en direct dans le
   terminal), puis construction et sauvegarde de l'index Faiss dans `./models/faiss_index/`
   (partagé avec les conteneurs via un volume monté). Si l'index existe déjà, cette étape est
   sautée.
3. Démarre les conteneurs `api` (port `8001`) et `ui` (port `8502`) et attend qu'ils soient
   opérationnels (`--wait`).

Comme l'index est construit et écrit sur le volume partagé *avant* que le conteneur `api` ne
démarre, celui-ci le charge normalement à son démarrage (voir son `lifespan` dans
`src/api/main.py`) — pas de redémarrage manuel nécessaire.

Pour arrêter : `make down`. Pour forcer un nouveau rebuild sur une instance déjà démarrée (par
exemple pour rafraîchir le corpus avec de nouveaux événements) : `make rebuild`, ou le bouton
« Reconstruire l'index » dans l'UI.

## Alternative sans Docker

```bash
uv sync --dev
make build-index   # équivalent local de l'étape de seeding, sans conteneur
uv run uvicorn api.main:app --reload --port 8001
uv run streamlit run src/ui/app.py --server.port 8502
```

## Structure du repo

```
src/api/            # API FastAPI (ports & adapters — voir Architecture)
src/ui/              # Interface Streamlit
src/notebooks/       # Code partagé notebooks (ex. prompts de recherche)
notebooks/           # Notebooks 01 à 07 : exploration → nettoyage → chunking → embeddings →
                      # chaîne RAG → évaluation RAGAS → optimisation MLflow
scripts/             # Scripts CLI (build_index.py)
tests/               # unit/, api/, integration/, eval/ (RAGAS)
data/                # Données brutes/intermédiaires (gitignored, sauf fixtures de test)
models/faiss_index/  # Index Faiss construit (gitignored)
reports/             # Rapport technique + script de démo (livrables certification)
docs/                # Cette documentation (mkdocs)
```

## Tests

```bash
make test-fast    # unit + api, rapide, aucune dépendance externe
make test-env     # suite complète incl. integration/ragas_ci, nécessite MISTRAL_API_KEY
```
