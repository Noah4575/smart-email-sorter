from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

# 1. Définir le schéma attendu
class FileClassification(BaseModel):
    category: str = Field(description="Catégorie : Factures, Projets, Cours, Admin, Divers")
    suggested_filename: str = Field(description="Nouveau nom de fichier propre en snake_case (ex: facture_edf_2026.pdf)")
    summary: str = Field(description="Court résumé en une phrase")

# 2. Instancier le LLM local
llm = ChatOllama(model="qwen3.5:4b", temperature=0)
structured_llm = llm.with_structured_output(FileClassification)

# 3. Tester sur un extrait de texte fictif
sample_text = "Facture EDF pour le mois de Septembre 2026. Montant total à payer: 45.20 EUR. Date de prélèvement: 05/10/2026."
res = structured_llm.invoke(f"Analyse et classifie ce contenu de fichier :\n{sample_text}")

print("Catégorie :", res.category)
print("Nom suggéré :", res.suggested_filename)
print("Résumé :", res.summary)