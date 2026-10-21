"""Run VoltPro's Vercel build steps and register the production Telegram hook."""

import os
import subprocess
import sys


def run(*args):
    subprocess.run([sys.executable, "manage.py", *args], check=True)


def main():
    production_bot_enabled = (
        os.environ.get("VERCEL_ENV") == "production"
        and bool(os.environ.get("TELEGRAM_BOT_TOKEN"))
    )
    if production_bot_enabled and not os.environ.get("DATABASE_URL"):
        raise SystemExit(
            "Telegram is enabled for production, but DATABASE_URL is missing. "
            "Configure the persistent PostgreSQL connection in Vercel."
        )

    run("migrate", "--noinput")
    run("collectstatic", "--noinput", "--clear")

    # Only the production deployment owns the Telegram webhook. A configured
    # token opts the project into the bot, and the command validates every
    # remaining required setting before making the Telegram API request.
    if production_bot_enabled:
        run("set_telegram_webhook", "https://voltpro.co.ke/telegram/webhook/")
    elif os.environ.get("VERCEL_ENV") == "production":
        print("Telegram webhook registration skipped: TELEGRAM_BOT_TOKEN is not configured.")


if __name__ == "__main__":
    main()
