from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class AskRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"question": "Quels concerts sont prévus en Île-de-France ce mois-ci ?"}]
        }
    )

    question: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
        Field(description="Question en langage naturel sur les événements culturels indexés."),
    ]


class SourceRefSchema(BaseModel):
    uid: str = Field(description="Identifiant unique du document parent (événement) source.")


class AskResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "question": "Quels concerts sont prévus en Île-de-France ce mois-ci ?",
                    "answer": "Voici quelques concerts à venir en Île-de-France : ...",
                    "sources": [{"uid": "evt-12345"}],
                }
            ]
        }
    )

    question: str = Field(description="La question telle qu'elle a été reçue.")
    answer: str = Field(description="Réponse générée par le LLM à partir des sources récupérées.")
    sources: list[SourceRefSchema] = Field(
        description="Documents parents utilisés comme contexte pour générer la réponse."
    )
