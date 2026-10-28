# Smart Email Sorter

A small Python command-line app that connects to an email inbox over IMAP,
finds unread messages, applies a category label based on the sender's email
domain, and then marks recognized messages as read and archives them.

The current sorter is deterministic: it does not ask an AI model to classify
messages. It uses the sender domain map below. It is intended for personal use
and currently uses Gmail-specific IMAP label extensions.

## What it does

For each run, the app:

1. Connects securely to the configured IMAP server and selects `INBOX`.
2. Searches for unread messages and fetches at most the 10 most recent matches.
   The message body is fetched with `BODY.PEEK[]`, which does not itself mark
   the message as read.
3. Extracts the sender address and maps its domain to a label:

   | Sender domain | Label |
   | --- | --- |
   | `email.openai.com` (including subdomains) | `ChatGPT` |
   | `instagram.com` (including subdomains) | `Instagram` |
   | `twitch.tv` (including subdomains) | `Twitch` |
   | `linkedin.com` (including subdomains) | `LinkedIn` |
   | `google.com` (including subdomains) | `Google` |

4. For a recognized domain, applies the label, marks the message as read, and
   removes the Gmail `INBOX` label to archive it. The label operation itself
   also marks the message as read before applying the label.
5. Skips unrecognized sender domains without changing those messages.

If applying a label fails, the error is printed and processing continues with
the next message. Since the label operation marks the message as read before
setting the label, a label failure may still leave the message marked read.
If marking as read or archiving fails, the error is printed and processing
continues; earlier successful changes are not rolled back. Review the
per-message output and mailbox if an operation fails.

The sender's `From` header is used for classification. This is a simple
convenience rule, not sender authentication; do not treat a label as proof that
an email is genuinely from a service.

## Requirements

Choose either local Python or Docker:

- **Local:** Python 3.13 (the version used by CI), pip, and network access to
  your IMAP server.
- **Docker:** Docker Desktop with Docker Compose enabled, and network access
  from Docker to your IMAP server.

The app needs IMAP over SSL (normally port 993). No web server or inbound port
is used.

## Configure credentials

Create a `.env` file in the project root (next to `requirements.txt`) with:

```dotenv
EMAIL_USER=your-email@example.com
EMAIL_PASSWORD=your-email-password-or-app-password
IMAP_SERVER=imap.gmail.com
```

`EMAIL_USER` and `EMAIL_PASSWORD` are required. `IMAP_SERVER` is optional and
defaults to `imap.gmail.com`. For a Gmail account with two-step verification,
use a Google app password rather than your normal account password, and make
sure IMAP access is available for the account.

Keep `.env` private. It is excluded from Git and Docker build context; Compose
reads it from the host and passes its values to the app container at runtime.
Never paste credentials into source code, commit them, or include them in logs
or screenshots.

## Run locally

From the project directory, create and activate a virtual environment, then
install dependencies:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the sorter:

```powershell
python -m app.agent
```

The program prints the number of unread messages found and the actions or
errors for each one. It exits when the current batch is finished. Run it again
manually when you want to process another batch.

## Run with Docker Compose

With Docker Desktop running and the root `.env` file configured:

```powershell
docker compose run --build --rm app
```

This builds the image if needed, runs one batch, prints progress in the
terminal, and removes the stopped container. The service is intentionally a
one-shot job: it does not run continuously, schedule itself, or restart after
completion. Run the command again for another batch.

To rebuild after changing dependencies or application code:

```powershell
docker compose build --no-cache
```

There is no Ollama service in Compose. Although the repository contains an
Ollama/LiteLLM configuration module and related dependencies, the current
`app.agent` sorter does not load or call an LLM.

## Important behavior and limitations

- Only unread messages in `INBOX` are considered.
- Only the 10 most recent unread messages are fetched in a run.
- Only domains in the mapping above are processed. Other senders remain
  unread and in the inbox until the mapping or behavior is changed.
- A recognized email is labeled, marked read, and archived. These operations
  modify the mailbox and may not be reversible from the app. A failure can
  leave a message partially processed.
- Gmail's `X-GM-LABELS` IMAP extension is used for labels and archiving;
  another IMAP provider may not support these operations.
- The message body is fetched and truncated to 500 characters by the IMAP
  helper, but the current label rules use only the sender address.
- The app is a local command-line utility, not a hosted web service. Do not
  expose IMAP credentials or this application to the public internet.

## Project layout

```text
.
├── app/
│   ├── agent.py       # Sequential processing and sender-domain rules
│   ├── config.py      # Legacy Ollama/LiteLLM configuration
│   └── mcp_server.py  # IMAP connection, fetch, label, read, and archive tools
├── .env               # Local credentials; create this yourself, do not commit
├── Dockerfile         # Python container image
├── docker-compose.yml # One-shot app service
├── requirements.txt   # Python dependencies
└── .github/workflows/ci.yml
```

## CI and checks

GitHub Actions installs the dependencies with Python 3.13 and runs a smoke
check that imports `app.config`, `app.agent`, and `app.mcp_server`. It does not
connect to an email account or run mailbox integration tests.

You can run the same import check locally:

```powershell
python -c "import app.config; import app.agent; import app.mcp_server; print('Imports OK')"
```

## Troubleshooting

### `EMAIL_USER and EMAIL_PASSWORD must be set`

Check that `.env` exists in the project root and contains both variables.
When using Docker Compose, run the command from the project directory so
Compose finds that file.

### IMAP authentication or connection fails

Verify the account name, password or app password, IMAP server, and that IMAP
access is enabled. Confirm your computer has network access to the IMAP server
over SSL (normally port 993). Do not share the password when requesting help.

### Labels or archive operation fail

These features use Gmail's IMAP extensions. Check the printed error and verify
that the configured provider supports Gmail-compatible `X-GM-LABELS`.

### No emails are processed

The current run only searches unread messages in `INBOX`, and only processes
the 10 most recent. Messages from sender domains outside the mapping are
intentionally skipped. Messages already marked read or archived will not be
selected by the next run.
