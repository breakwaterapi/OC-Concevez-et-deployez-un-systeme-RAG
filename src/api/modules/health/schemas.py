from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description='"ok" si tout est prêt, "degraded" sinon.')
    store_ready: bool = Field(description="True si l'index Faiss est construit et chargé.")
    model_ready: bool = Field(description="True si l'API Mistral répond correctement.")
    index_size: int = Field(description="Nombre de vecteurs (chunks) actuellement dans l'index.")
