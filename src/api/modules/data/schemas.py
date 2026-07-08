from pydantic import BaseModel, Field


class RebuildResponse(BaseModel):
    status: str = Field(
        description='Toujours "ok" si la requête aboutit (sinon une erreur HTTP est renvoyée).'
    )
    n_chunks: int = Field(description="Nombre de chunks (vecteurs Faiss) construits.")
    n_parent_docs: int = Field(description="Nombre de documents parents (événements) indexés.")
    message: str = Field(description="Résumé lisible du résultat de la reconstruction.")
