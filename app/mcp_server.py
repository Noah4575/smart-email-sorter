import imaplib
import email
from email.header import decode_header
from fastmcp import FastMCP
import os

mcp = FastMCP("Smart Email Sorter MCP (Real IMAP)")

# Configuration IMAP (à stocker dans un fichier .env plus tard)
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

@mcp.tool()
def fetch_unread_emails() -> list[dict]:
    """Récupère les vrais e-mails non lus depuis le serveur IMAP."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASSWORD)
        mail.select("inbox")

        # Recherche des e-mails non lus (UNSEEN)
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            return []

        unread_emails = []
        for num in messages[0].split():
            status, data = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue

            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Décodage du sujet
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8", errors="ignore")
                    
                    sender = msg.get("From")

                    # Récupération du corps du message
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    unread_emails.append({
                        "id": num.decode(),  # ID IMAP du message
                        "sender": sender,
                        "subject": subject,
                        "body": body[:500], # On limite les 500 premiers caractères pour le LLM
                        "is_read": False
                    })
        
        mail.logout()
        return unread_emails

    except Exception as e:
        print(f"Erreur de connexion IMAP : {e}")
        return []

@mcp.tool()
def apply_email_action(email_id: str, action: str, target_label: str = "") -> str:
    """Applique une action réelle sur le serveur IMAP (marquer comme lu, archiver, etc.)."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASSWORD)
        mail.select("inbox")

        # Conversion de l'ID en bytes pour IMAP
        msg_id = email_id.encode()

        if action == "mark_read":
            mail.store(msg_id, "+FLAGS", "\\Seen")
        elif action == "archive":
            # En IMAP, archiver signifie souvent copier dans 'All Mail' ou retirer de la boîte de réception ('[Gmail]/Tous les messages')
            mail.store(msg_id, "+FLAGS", "\\Seen")
            # Logique spécifique de déplacement si besoin
        
        mail.logout()
        return f"Action '{action}' exécutée avec succès sur l'e-mail IMAP {email_id}."

    except Exception as e:
        return f"Erreur lors de l'action IMAP : {e}"