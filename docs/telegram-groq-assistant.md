# Private Telegram quote and invoice assistant

The bot uses Groq to understand owner prompts and offers a narrow set of tools: search quotes, search invoices, look up active inventory prices, prepare draft quotes, and prepare invoice conversion for accepted quotes. It has no arbitrary Django admin, shell, file, website, or settings access. All writes require the allowlisted owner to send a short-lived `/confirm CODE` in the same private Telegram chat.

## Vercel setup

1. Store these encrypted environment variables in the Vercel project. If a bot token has been shared in chat, rotate it with BotFather before adding the replacement.

   - `TELEGRAM_BOT_TOKEN` — replacement bot token from BotFather.
   - `TELEGRAM_ALLOWED_USER_ID` — your numeric Telegram user ID. The bot ignores groups and all other users.
   - `TELEGRAM_WEBHOOK_SECRET` — a random 1–256 character value containing only letters, numbers, underscores, and hyphens. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
   - `GROQ_API_KEY` — Groq API key.
   - `GROQ_MODEL` — optional; defaults to `llama-3.3-70b-versatile`.

2. Deploy the site so the webhook endpoint is available at `https://<your-domain>/telegram/webhook/`.
3. On a trusted machine with the same four environment variables available, register the endpoint once:

   ```powershell
   python manage.py migrate
   python manage.py set_telegram_webhook https://<your-domain>/telegram/webhook/
   ```

   The command sends the secret token to Telegram's `setWebhook` API; the app validates that secret on every incoming webhook request. Stop any old `run_telegram_assistant` polling process before registering the webhook. Do not run polling and webhook delivery together.

Vercel functions handle individual requests with a maximum runtime, so Telegram webhooks are used instead of a permanent long-polling worker.

## Use

- Send `/help` to see supported requests.
- Ask naturally, for example “show recent quotes”, “find VP-2026-0044”, or “look up 5 kW inverter in inventory”.
- To prepare a draft quote, include the client details and each item's description, quantity, and price. Active catalog items use the current catalog price. Custom lines require a price in the prompt. The assistant displays the quote, including the KRA PIN when provided, and waits for confirmation.
- To prepare an invoice, ask to convert an accepted quote by its quote number. The bot checks that it is still accepted before preparing and again when saving.
- Send `/confirm CODE` within 10 minutes to make the staged change and receive its PDF, or `/cancel` to discard it.

Prompts and the minimum quote/inventory information needed to answer them are sent to Groq. The bot is intended for one trusted owner; keep all provider tokens and webhook secrets in Vercel's encrypted environment settings.
