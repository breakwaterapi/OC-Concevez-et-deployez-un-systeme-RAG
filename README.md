# Puls-Events — Assistant RAG pour événements culturels

POC d'un chatbot **RAG (Retrieval-Augmented Generation)** répondant à des questions sur les
événements culturels à venir en **Île-de-France**, à partir des données publiques
[Open Agenda](https://public.opendatasoft.com/explore/dataset/evenements-publics-openagenda/table/).

Le système combine une recherche vectorielle **Faiss** sur les descriptions d'événements et une
génération de réponse en langage naturel avec **Mistral** (via **LangChain**), exposée par une
**API REST FastAPI**.

Projet réalisé dans le cadre de la certification OpenClassrooms *Concevez et déployez un système
RAG*. Documentation complète (architecture détaillée, référence API, évaluation) : `make docs`
(sert `http://localhost:8000` en local) ou directement les fichiers sous `docs/`.

## Pour l'examinateur

1. `make up` — une seule commande : build des images, seeding de l'index avec barre de progression
   si absent, démarrage de l'API + UI. Voir [Docker](#docker) pour le détail.
2. Swagger : http://localhost:8001/docs — chaque endpoint est documenté (paramètres, réponses,
   codes d'erreur).
3. UI de démo : http://localhost:8502.
4. Rapport technique complet : [`reports/rapport_technique.md`](reports/rapport_technique.md).
5. Script de démo (4 scénarios commentés) : [`reports/demo_script.md`](reports/demo_script.md).
6. Documentation détaillée (architecture, rôle de chaque composant) : `make docs`, ou
   [`docs/architecture.md`](docs/architecture.md) directement.

## Sommaire

- [Architecture](#architecture)
- [Structure du projet](#structure-du-projet)
- [Installation](#installation)
- [Construire l'index vectoriel](#construire-lindex-vectoriel)
- [Lancer l'API et l'UI](#lancer-lapi-et-lui)
- [Tests](#tests)
- [Évaluation (RAGAS)](#évaluation-ragas)
- [Docker](#docker)

## Architecture

```
[ 👤 UTILISATEUR ]                              [ 📅 OPEN AGENDA API ]
        │                                                  │
        │ (1. Pose une question)                           │ (A. Extraction)
        ▼                                                  ▼
┌──────────────────────────────┐                ┌──────────────────────────────┐
│    FASTAPI : ENDPOINT /ask   │                │      DOCLING : NETTOYAGE     │
└──────────────┬───────────────┘                └──────────┬───────────────────┘
               │                                           │
               │ (2. Vectorise la question)                │ (B. Découpage en morceaux)
               ▼                                           ▼
┌──────────────────────────────┐                ┌──────────────────────────────┐
│ MISTRAL EMBEDDINGS (Query)   │                │           CHUNKING           │
└──────────────┬───────────────┘                └──────┬───────────────┬───────┘
               │                                       │               │
               │ (3. Cherche vecteurs proches)         │               │ (C. Extraction texte complet)
               ▼                                       │               │
┌──────────────────────────────────────────────────────┼───────────────┼───────┐
│ COUCHE DE STOCKAGE (Bases de données)                │               │       │
│                                                      ▼               │       │
│              ┌──────────────────────────────┐   ┌────┴────────────┐  │       │
│              │     INDEX VECTORIEL FAISS    │◀──┤ MISTRAL EMBED   │  │       │
│              └──────────────┬───────────────┘   └─────────────────┘  │       │
│                             │                                        ▼       │
│                             │ (4. Renvoie IDs Top-K)       ┌────────────────┐│
│                             ▼                              │  PARENT DOCS   ││
│        ┌──────────────────────────────────────────────────▶│  MAGASIN TEXTE ││
│        │                                                   └───────┬────────┘│
│        │ (5. Récupère le texte complet via les IDs)                │         │
└────────┼───────────────────────────────────────────────────────────┼─────────┘
         │                                                           │
         │                                                           │ (6. Renvoie les textes)
         ▼                                                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ API FASTAPI : CONSTRUCTION DU PROMPT (Question + Textes de Parent Docs)      │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       │ (7. Envoie le Prompt complet)
                                       ▼
                        ┌──────────────────────────────┐
                        │     MISTRAL LLM (Génération) │
                        └──────────────┬───────────────┘
                                       │
                                       │ (8. Réponse finale)
                                       ▼
                                [ 👤 UTILISATEUR ]
```

Le code applicatif (`src/api`) suit une architecture en couches (ports & adapters) :

- **`modules/`** — logique métier par domaine (`rag`, `data`, `documents`, `health`), chacun avec ses
  `use_cases`, `ports` (interfaces) et `router` (FastAPI).
- **`infra/`** — implémentations concrètes des ports : client Open Agenda, nettoyage Docling,
  chunking LangChain, embeddings/LLM Mistral, store Faiss.
- **`bootstrap.py`** — câblage des dépendances (injection) au démarrage de l'application.

Les notebooks (`notebooks/01` à `07`) documentent la construction pas à pas du pipeline
(exploration → nettoyage → chunking → embeddings → chaîne RAG → évaluation RAGAS → optimisation
MLflow) avant sa consolidation dans `src/api`.

## Structure du projet

```
├── src/
│   ├── api/            API FastAPI (RAG, ingestion, documents, health)
│   ├── ui/             Interface de démo Streamlit
│   └── notebooks/      Utilitaires partagés par les notebooks (config, MLflow)
├── notebooks/          Notebooks d'exploration et de construction du pipeline (01 à 07)
├── tests/
│   ├── unit/           Tests unitaires (chunking, Faiss, use cases RAG/data/health)
│   ├── api/            Tests fonctionnels de l'API (FastAPI TestClient)
│   └── integration/    Test bout-en-bout (Mistral + Faiss réels, nécessite une clé API)
├── scripts/             build_index.py — construit l'index sans passer par l'API (utilisé par `make up`)
├── data/                Données brutes/intermédiaires/traitées/évaluation (non versionnées)
├── models/faiss_index/  Index Faiss + métadonnées des documents (généré par /rebuild)
├── reports/             Rapport technique et figures (livrables certification)
├── docs/                Documentation mkdocs (architecture, référence API, évaluation)
├── Dockerfile, docker-compose.yml
└── pyproject.toml       Dépendances (gérées avec uv)
```

## Installation

Prérequis : Python 3.12, [uv](https://docs.astral.sh/uv/).

```bash
uv sync --dev
cp .env.example .env
# Renseignez MISTRAL_API_KEY dans .env (clé obtenue sur https://console.mistral.ai/)
```

Vérifiez que l'environnement fonctionne :

```bash
uv run python -c "import faiss, langchain, mistralai; print('OK')"
```

## Construire l'index vectoriel

L'index Faiss n'est pas versionné (voir `.gitignore`) : il doit être (re)construit localement.
Plusieurs façons de le faire :

- **`make build-index`** — script autonome (`scripts/build_index.py`), sans passer par l'API.
- **Via l'API**, une fois celle-ci lancée : bouton *« Reconstruire l'index »* dans l'UI, ou

  ```bash
  curl -X POST http://localhost:8001/rebuild -H "X-API-Key: $REBUILD_API_KEY"
  ```

- **Via les notebooks** (`02` à `05`) pour explorer chaque étape du pipeline en détail.

Cela récupère les événements Open Agenda (Île-de-France, ±1 an autour de `REFERENCE_DATE`), les
nettoie, les découpe en chunks, les vectorise avec `mistral-embed`, et sauvegarde l'index dans
`models/faiss_index/`.

## Lancer l'API et l'UI

```bash
uv run uvicorn api.main:app --reload --port 8001
uv run streamlit run src/ui/app.py --server.port 8502
```

- Documentation interactive (Swagger) : http://localhost:8001/docs
- UI de démo : http://localhost:8502

Endpoints principaux :

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/ask` | Pose une question, renvoie une réponse générée + sources |
| `POST` | `/rebuild` | Reconstruit l'index vectoriel à partir des données Open Agenda — protégé, nécessite le header `X-API-Key: <REBUILD_API_KEY>` |
| `GET` | `/health` | État de l'API (index prêt, modèle joignable, taille de l'index) |
| `GET` | `/metadata` | Métadonnées du corpus indexé (région, période couverte, tailles, modèles) |
| `GET` | `/documents` / `/documents/{uid}` | Consulte les documents indexés |
| `GET` | `/retrieve?q=...` | Recherche sémantique brute (sans génération) |

## Tests

```bash
make test-fast     # unitaires + API (rapides, sans dépendance externe)
make test           # inclut aussi les tests d'intégration (nécessite MISTRAL_API_KEY + index Faiss)
```

## Évaluation (RAGAS)

Un jeu de **15 questions annotées** (10 nominales + 5 pièges, `data/evaluation/test_questions.json`)
est évalué avec le framework [RAGAS](https://docs.ragas.io/) (`faithfulness`, `answer_relevancy`,
`context_recall`, `context_precision`, `context_entity_recall`) dans
`notebooks/06.0-kl-evaluation.ipynb`, contre un **snapshot figé** de l'index
(`data/evaluation/eval_faiss_index/`, indépendant de l'index de production). Les résultats sont
sauvegardés dans `data/evaluation/` et suivis dans **MLflow**
(`notebooks/07.0-kl-mlflow-optimization.ipynb`) pour comparer les configurations (chunking, `k` de
retrieval, prompts) — cette dernière étape reste une trace exploratoire, antérieure à la refonte du
prompt de production.

Un sous-ensemble réduit (4 questions, dont une hors corpus, `data/evaluation/test_questions_ci.json`)
sert de contrôle rapide local ou en CI (`tests/eval/test_ragas_ci.py`, marqueur `ragas_ci`, skip
automatique sans `MISTRAL_API_KEY`).

## Docker

L'index Faiss n'est pas construit dans l'image. `make up` :

1. Construit les images (`docker compose build`).
2. Si `models/faiss_index/index.faiss` est absent, lance un **conteneur éphémère** qui exécute
   `scripts/build_index.py` (même code que `/rebuild`, réutilisé via `api.bootstrap`) : ce
   conteneur tourne en avant-plan, donc la **barre de progression** de l'étape d'embedding
   s'affiche en direct dans le terminal. Comme il écrit sur le volume `./models` partagé avec le
   conteneur `api`, et que celui-ci ne démarre qu'après, l'index construit est garanti d'être
   chargé correctement au démarrage de l'API — pas de redémarrage manuel nécessaire.
3. Démarre `api` (:8001) et `ui` (:8502) et attend qu'ils soient prêts (`--wait`).

Le volume `./models` est monté pour persister l'index entre les redémarrages.

```bash
make up             # build + seed si nécessaire (progress bar) + démarre API/UI
make down           # arrêt et suppression complète des conteneurs
```

Cibles plus fines si besoin :

```bash
make rebuild        # force un rebuild via /rebuild sur les conteneurs déjà lancés (rafraîchir le corpus)
make build-index    # (re)construit l'index localement (uv, sans Docker ni conteneurs)
make docs           # sert la documentation mkdocs en local (http://localhost:8000)
make docker-build
make docker-up
make docker-down
```
