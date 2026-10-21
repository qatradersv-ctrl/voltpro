# Private Telegram quote and invoice assistant

The bot uses Groq to understand owner prompts and offers a narrow set of tools: search quotes, search invoices, look up active inventory prices, prepare draft quotes, and prepare invoice conversion for accepted quotes. It has no arbitrary Django admin, shell, file, website, or settings access. All writes require the allowlisted owner to send a short-lived `/confirm CODE` in the same private Telegram chat.

## Configure

1. Create a Telegram bot with [BotFather](https://t.me/BotFather) and keep its token private.
2. Get a Groq API key from the [Groq console](https://console.groq.com/keys).
3. Set these environment variables on the Django server. Do not paste secrets into Telegram, source files, or Git:

   - `TELEGRAM_BOT_TOKEN` — token from BotFather.
   - `TELEGRAM_ALLOWED_USER_ID` — the owner's numeric Telegram user ID. The bot ignores groups and every other user.
   - `GROQ_API_KEY` — Groq API key.
   - `GROQ_MODEL` — optional; defaults to `llama-3.3-70b-versatile`.

4. Apply Django migrations, then run exactly one persistent worker alongside the web app:

   ```powershell
   python manage.py migrate
   python manage.py run_telegram_assistant
   ```

The worker uses Telegram long polling and stores its update cursor and pending confirmation in Django's database. Keep it running with your process manager on an always-on host; serverless request-only hosting cannot keep a polling worker alive. Do not run multiple polling workers for the same bot token.

## Use

- Send `/help` to see supported requests.
- Ask naturally, for example “show recent quotes”, “find VP-2026-0044”, or “look up 5 kW inverter in inventory”.
- To prepare a draft quote, include the client details and each item's description, quantity, and price. Active catalog items use the current catalog price. Custom lines require a price in the prompt. The assistant displays the quote, including the KRA PIN when provided, and waits for confirmation.
- To prepare an invoice, ask to convert an accepted quote by its quote number. The bot checks that it is still accepted before preparing and again when saving.
- Send `/confirm CODE` within 10 minutes to make the staged change and receive its PDF, or `/cancel` to discard it.

Prompts and the minimum quote/inventory information needed to answer them are sent to Groq. The bot is intended for one trusted owner; use the Telegram user ID allowlist and keep both provider tokens in deployment secrets.
