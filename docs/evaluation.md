# Évaluation

L'évaluation détaillée (méthodologie complète, résultats chiffrés, interprétation) est dans
`reports/rapport_technique.md` (à la racine du repo). Cette page résume l'approche.

## Méthodologie

- **Framework** : [RAGAS](https://docs.ragas.io/), avec Mistral comme juge LLM (`mistral-medium-latest`)
  et comme modèle d'embeddings du juge.
- **Métriques** : `faithfulness` (la réponse est-elle fidèle au contexte récupéré ?),
  `answer_relevancy` (la réponse répond-elle à la question ?), `context_recall`/`context_precision`
  (le retrieval a-t-il trouvé les bons documents ?), `context_entity_recall`.
- **Notebooks** :
  - `notebooks/06-*.ipynb` — construction de la chaîne RAG complète et tests de robustesse
    (prompt injection, questions hors périmètre, questions sans réponse dans le corpus).
  - `notebooks/07-*.ipynb` — évaluation RAGAS sur un jeu de questions de référence et
    exploration MLflow des hyperparamètres (taille/recouvrement des chunks, `k` de retrieval,
    formulation du prompt système).
- **Non-régression en CI** : `tests/eval/test_ragas_ci.py` — une évaluation réduite (4 questions,
  seuils de smoke-test) sur un corpus fixe versionné (`tests/fixtures/documents.json`), pour
  détecter une régression de prompt/retrieval sans dépendre du corpus complet (qui n'est pas
  commité). Nécessite `MISTRAL_API_KEY` (`make test-env` ou `pytest -m ragas_ci`).

## Configuration retenue en production

Issue de l'exploration MLflow du notebook 07 (voir `src/api/common/config.py`) :

- Chunking : `CHUNK_MAX_TOKENS=256`, `CHUNK_OVERLAP_TOKENS=20`.
- Retrieval : `k=5` par défaut.
- Prompt système : version structurée (rôle, objectif, limites explicites incluant des
  instructions anti-injection de prompt, style de communication) — voir
  `src/api/modules/rag/prompts.py`.
