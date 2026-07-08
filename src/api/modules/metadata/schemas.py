from pydantic import BaseModel, Field


class MetadataResponse(BaseModel):
    region: str = Field(description="Région Open Agenda couverte par l'index.")
    date_from: str = Field(
        description="Borne inférieure (ISO 8601) de la fenêtre d'événements indexée."
    )
    date_to: str = Field(
        description="Borne supérieure (ISO 8601) de la fenêtre d'événements indexée."
    )
    n_events: int = Field(description="Nombre de documents parents (événements) indexés.")
    n_chunks: int = Field(description="Nombre de chunks (vecteurs Faiss) indexés.")
    embed_model: str = Field(description="Modèle Mistral utilisé pour les embeddings.")
    chat_model: str = Field(description="Modèle Mistral utilisé pour la génération de réponse.")
