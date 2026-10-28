import imaplib
import email
from email.header import decode_header
from fastmcp import FastMCP
from contextlib import contextmanager
from dotenv import load_dotenv
import os
from typing import Iterator

load_dotenv()

mcp = FastMCP("Smart Email Sorter MCP (Real IMAP)")

# Configuration IMAP (à stocker dans un fichier .env plus tard)
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


@contextmanager
def _inbox_connection() -> Iterator[imaplib.IMAP4_SSL]:
    if not EMAIL_USER or not EMAIL_PASSWORD:
        raise RuntimeError("EMAIL_USER and EMAIL_PASSWORD must be set.")

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    authenticated = False
    try:
        mail.login(EMAIL_USER, EMAIL_PASSWORD)
        authenticated = True
        status, _ = mail.select("INBOX")
        if status != "OK":
            raise RuntimeError("Could not select the INBOX mailbox.")
        yield mail
    finally:
        if authenticated:
            mail.logout()


def _store(
    mail: imaplib.IMAP4_SSL, email_id: str, operation: str, value: str
) -> None:
    status, _ = mail.uid("STORE", email_id, operation, value)
    if status != "OK":
        raise RuntimeError(f"IMAP STORE failed for email ID {email_id}.")


@mcp.tool()
def fetch_unread_emails() -> list[dict]:
    """Récupère les vrais e-mails non lus depuis le serveur IMAP."""
    with _inbox_connection() as mail:
        status, messages = mail.uid("SEARCH", None, "UNSEEN")
        if status != "OK":
            raise RuntimeError("Could not search for unread emails.")

        message_ids = messages[0].split()
        mail_limit = 10
        recent_message_ids = (
            message_ids[-mail_limit:]
            if len(message_ids) > mail_limit
            else message_ids
        )

        unread_emails = []
        for uid in recent_message_ids:
            status, data = mail.uid("FETCH", uid, "(BODY.PEEK[])")
            if status != "OK":
                raise RuntimeError(
                    f"Could not fetch unread email ID {uid.decode('ascii')}."
                )

            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    decoded_subject = decode_header(msg.get("Subject", ""))
                    subject, encoding = decoded_subject[0] if decoded_subject else ("", None)
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8", errors="ignore")

                    sender = msg.get("From")

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body = payload.decode(errors="ignore")
                                break
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode(errors="ignore")

                    unread_emails.append(
                        {
                            "id": uid.decode("ascii"),
                            "sender": sender,
                            "subject": subject,
                            "body": body[:500],
                            "is_read": False,
                        }
                    )

        return unread_emails


@mcp.tool()
def mark_email_as_read(email_id: str) -> str:
    """Marque un e-mail comme lu sur le serveur IMAP."""
    with _inbox_connection() as mail:
        _store(mail, email_id, "+FLAGS", "\\Seen")
    return f"E-mail IMAP ID {email_id} marqué comme lu."


@mcp.tool()
def apply_email_label(email_id: str, target_label: str) -> str:
    """Applique un libellé Gmail à un e-mail sur le serveur IMAP."""
    with _inbox_connection() as mail:
        _store(mail, email_id, "+FLAGS", "\\Seen")
        label_payload = f'("{target_label}")'
        _store(mail, email_id, "+X-GM-LABELS", label_payload)
    return f"Libellé '{target_label}' appliqué à l'e-mail IMAP ID {email_id}."


@mcp.tool()
def archive_email(email_id: str) -> str:
    """Archive un e-mail Gmail en le retirant de la boîte de réception."""
    with _inbox_connection() as mail:
        _store(mail, email_id, "+FLAGS", "\\Seen")
        _store(mail, email_id, "-X-GM-LABELS", r"(\Inbox)")
    return f"E-mail IMAP ID {email_id} archivé."