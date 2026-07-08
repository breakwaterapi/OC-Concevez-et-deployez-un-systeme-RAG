from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


class SourceSchema(BaseModel):
    uid: str = Field(description="Identifiant unique du document parent (événement).")
    text: str = Field(description="Texte complet du document parent (description de l'événement).")


class ListDocumentsParams(BaseModel):
    limit: int = Field(
        default=20, ge=1, le=500, description="Nombre maximum de documents renvoyés."
    )
    offset: int = Field(default=0, ge=0, description="Nombre de documents à sauter (pagination).")


class RetrieveParams(BaseModel):
    q: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1),
        Field(description="Requête en langage naturel pour la recherche sémantique."),
    ]
    k: int = Field(default=5, ge=1, le=50, description="Nombre de documents à renvoyer.")
