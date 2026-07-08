# Puls-Events — Assistant RAG pour événements culturels

POC d'un chatbot **RAG (Retrieval-Augmented Generation)** répondant à des questions sur les
événements culturels à venir en **Île-de-France**, à partir des données publiques
[Open Agenda](https://public.opendatasoft.com/explore/dataset/evenements-publics-openagenda/table/).
Le système combine une recherche vectorielle **Faiss** et une génération de réponse avec
**Mistral** (via **LangChain**), exposée par une **API REST FastAPI** et une UI **Streamlit**.

Projet réalisé dans le cadre de la certification OpenClassrooms *Concevez et déployez un système
RAG*.

## Pour l'examinateur

Un chemin de review complet, sans avoir besoin de lire le code au préalable :

1. **Lancer le projet** — une seule commande, depuis la racine du repo :

    ```bash
    make up
    ```

    Cette commande construit les images Docker, puis, si l'index vectoriel n'existe pas encore
    (`models/faiss_index/`), le construit via un conteneur dédié qui télécharge les événements
    Open Agenda et calcule leurs embeddings Mistral — une barre de progression s'affiche en
    direct dans le terminal pendant cette étape (qui peut prendre quelques minutes). Une fois
    l'index prêt, l'API et l'UI démarrent. Voir [Démarrage](getting-started.md) pour le détail.

2. **Explorer l'API** — documentation interactive générée automatiquement :
   [http://localhost:8001/docs](http://localhost:8001/docs) (Swagger) — chaque endpoint, ses
   paramètres et ses réponses possibles y sont documentés. Voir aussi
   [Référence API](api-reference.md) pour des exemples `curl`.

3. **Utiliser l'interface** : [http://localhost:8502](http://localhost:8502) — poser des
   questions, consulter les sources, déclencher une reconstruction de l'index.

4. **Comprendre l'architecture** : [Architecture](architecture.md) — diagramme du pipeline et
   rôle de chaque composant (ports, use cases, infra).

5. **Lire le rapport technique complet** : `reports/rapport_technique.md` (à la racine du repo)
   — contexte, choix technologiques, résultats d'évaluation, pistes d'amélioration.

6. **Suivre le script de démo** : `reports/demo_script.md` (à la racine du repo) — 4 scénarios de
   démonstration commentés, avec les questions/réponses attendues sur le corpus indexé.

7. **Résumé de l'évaluation RAGAS** : [Évaluation](evaluation.md).

## Sommaire de cette documentation

- [Démarrage](getting-started.md) — prérequis, `make up`, structure du repo.
- [Architecture](architecture.md) — diagramme et rôle de chaque composant.
- [Référence API](api-reference.md) — tour des endpoints avec exemples `curl`.
- [Évaluation](evaluation.md) — méthodologie et résultats RAGAS.
