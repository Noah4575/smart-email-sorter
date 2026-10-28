# Smart Email Sorter

## Run with Docker

Requirements: Docker Desktop with Docker Compose enabled.

The app reads IMAP settings from the root `.env` file. Keep this file private
and do not commit it. It should define `EMAIL_USER` and `EMAIL_PASSWORD`;
`IMAP_SERVER` is optional and defaults to `imap.gmail.com`.

Run the one-shot email sorter from the project directory:

```powershell
docker compose run --build --rm app
```

The container exits when it finishes processing. Run the command again when
you want to process the next batch. No ports need to be exposed. The current
`app.agent` processes mail directly over IMAP and does not require an Ollama
container.
