from email.utils import parseaddr

from app.mcp_server import (
    apply_email_label,
    archive_email,
    fetch_unread_emails,
    mark_email_as_read,
)

LABELS_BY_DOMAIN = {
    "email.openai.com": "ChatGPT",
    "instagram.com": "Instagram",
    "twitch.tv": "Twitch",
    "linkedin.com": "LinkedIn",
    "google.com": "Google",
}


def _label_for_sender(sender: str | None) -> str | None:
    _, address = parseaddr(sender or "")
    domain = address.rpartition("@")[2].lower().rstrip(".")

    for known_domain, label in LABELS_BY_DOMAIN.items():
        if domain == known_domain or domain.endswith(f".{known_domain}"):
            return label
    return None


def _apply_action(action_name: str, action, email_id: str) -> bool:
    try:
        result = action(email_id)
        print(f"  {action_name}: {result}")
        return True
    except Exception as error:
        print(f"  ERREUR {action_name}: {error}")
        return False


def process_unread_emails() -> None:
    emails = fetch_unread_emails()
    print(f"{len(emails)} e-mail(s) non lu(s) à traiter.")

    for item in emails:
        email_id = str(item["id"])
        sender = item.get("sender")
        label = _label_for_sender(sender)
        print(f"\n[{email_id}] {sender or '(expéditeur inconnu)'} — {item.get('subject', '')}")

        if label is None:
            print("  Ignoré: domaine expéditeur non reconnu; e-mail laissé inchangé.")
            continue

        print(f"  Catégorie déterministe: {label}")
        try:
            result = apply_email_label(email_id, label)
            print(f"  Libellé: {result}")
        except Exception as error:
            print(f"  ERREUR application du libellé: {error}")
            print("  E-mail conservé comme non lu et dans la boîte de réception.")
            continue

        _apply_action("Marquage comme lu", mark_email_as_read, email_id)
        _apply_action("Archivage", archive_email, email_id)

    print("\nTraitement terminé.")


if __name__ == "__main__":
    print("🚀 Lancement du tri Smart Email Sorter...")
    process_unread_emails()
