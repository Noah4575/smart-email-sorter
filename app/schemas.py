from pydantic import BaseModel, Field
from typing import Literal

class EmailClassification(BaseModel):
    category: str = Field(description="Catégorie principale : Newsletters, Projets, Administratif, Promotions, Urgent, Divers")
    summary: str = Field(description="Résumé concis de l'e-mail en une seule phrase")
    action: Literal["archive", "mark_read", "apply_label", "keep"] = Field(
        description="Action exacte à mener parmi la liste autorisée."
    )
    target_label: str = Field(description="Nom exact de l'étiquette à appliquer si l'action est apply_label, sinon chaîne vide")