from mcp.server.mcpserver import MCPServer

from app.data_store import EMAILS_DATABASE

# Initialisation du serveur MCP pour les e-mails
mcp = MCPServer("Smart Email Sorter MCP")



@mcp.tool()
def fetch_unread_emails() -> list[dict]:
    """Récupère la liste des e-mails non lus dans la boîte de réception."""
    unread = [email for email in EMAILS_DATABASE if not email["is_read"]]
    return unread

@mcp.tool()
def apply_email_action(email_id: str, action: str, target_label: str = "") -> str:
    """
    Applique une action sur un e-mail donné.
    Actions possibles : archive, mark_read, apply_label, keep.
    """
    for email in EMAILS_DATABASE:
        if email["id"] == email_id:
            if action in ["mark_read", "archive"]:
                email["is_read"] = True
            return f"Action '{action}' (étiquette: {target_label}) exécutée avec succès sur l'e-mail {email_id}."
    
    return f"Erreur : E-mail avec l'ID {email_id} introuvable."

if __name__ == "__main__":
    # Lancement du serveur MCP en transport stdio (standard pour les clients locaux)
    mcp.run()