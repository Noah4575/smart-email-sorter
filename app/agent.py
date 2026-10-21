import os
from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.config import get_llm
from app.schemas import EmailClassification
from app.mcp_server import fetch_unread_emails, apply_email_action

# 1. Définition de l'état global du graphe
class State(TypedDict):
    messages: list
    unread_emails: list
    processed_count: int

# 2. Initialisation du LLM via LiteLLM
llm = get_llm(temperature=0.0)
structured_llm = llm.with_structured_output(EmailClassification)

# 3. Définition des Nœuds du Graphe

def fetch_emails_node(state: State):
    """Nœud 1 : Récupère les e-mails non lus."""
    print("--- [AGENT] Récupération des e-mails non lus ---")
    emails = fetch_unread_emails()
    return {"unread_emails": emails, "processed_count": 0}

def process_emails_node(state: State):
    """Nœud 2 : Analyse et traite chaque e-mail avec le LLM local."""
    emails = state.get("unread_emails", [])
    
    if not emails:
        print("--- [AGENT] Aucun e-mail à traiter. ---")
        return {"messages": [HumanMessage(content="Aucun e-mail à traiter.")]}

    results = []
    for email in emails:
        print(f"\n--- Analyse de l'e-mail ID: {email['id']} de {email['sender']} ---")
        
        prompt = f"""
        Analyse l'e-mail suivant :
        - Expéditeur : {email['sender']}
        - Sujet : {email['subject']}
        - Corps : {email['body']}
        """
        
        # Appel au LLM local (Ollama via LiteLLM) avec structure Pydantic
        classification: EmailClassification = structured_llm.invoke(prompt)
        
        print(f"  -> Catégorie : {classification.category}")
        print(f"  -> Résumé : {classification.summary}")
        print(f"  -> Action recommandée : {classification.action} (Label: {classification.target_label})")
        
        # Exécution de l'action via l'outil
        action_result = apply_email_action(
            email_id=email['id'],
            action=classification.action,
            target_label=classification.target_label
        )
        print(f"  -> {action_result}")
        results.append(action_result)

    return {"messages": [HumanMessage(content=f"Traitement terminé pour {len(emails)} e-mails.")]}

# 4. Construction du Graphe LangGraph
workflow = StateGraph(State)

# Ajout des nœuds
workflow.add_node("fetch_emails", fetch_emails_node)
workflow.add_node("process_emails", process_emails_node)

# Définition du flux séquentiel
workflow.add_edge(START, "fetch_emails")
workflow.add_edge("fetch_emails", "process_emails")
workflow.add_edge("process_emails", END)

# Compilation de l'agent
agent_app = workflow.compile()

if __name__ == "__main__":
    # Test d'exécution locale de l'agent
    print("Lancement de l'agent Smart Email Sorter...")
    initial_state = {"messages": [], "unread_emails": [], "processed_count": 0}
    final_state = agent_app.invoke(initial_state)
    print("\nExécution du graphe terminée avec succès !")