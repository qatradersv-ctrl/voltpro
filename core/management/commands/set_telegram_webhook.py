import re
from urllib.parse import urlsplit

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.telegram_assistant import AssistantError, _telegram


class Command(BaseCommand):
    help = "Register the Telegram assistant webhook at the deployed HTTPS URL."

    def add_arguments(self, parser):
        parser.add_argument("url", help="Public HTTPS webhook URL, ending in /telegram/webhook/")

    def handle(self, *args, **options):
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "")
        if not token:
            raise CommandError("Set TELEGRAM_BOT_TOKEN in the environment.")
        if not getattr(settings, "TELEGRAM_ALLOWED_USER_ID", ""):
            raise CommandError("Set TELEGRAM_ALLOWED_USER_ID in the environment.")
        if not getattr(settings, "GROQ_API_KEY", ""):
            raise CommandError("Set GROQ_API_KEY in the environment.")
        if not secret or len(secret) > 256 or not re.fullmatch(r"[A-Za-z0-9_-]+", secret):
            raise CommandError("Set TELEGRAM_WEBHOOK_SECRET to 1–256 letters, numbers, underscores, or hyphens.")

        url = options["url"].strip()
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise CommandError("The webhook URL must be a public HTTPS URL without credentials, query parameters, or a fragment.")
        if not parsed.path.endswith("/telegram/webhook/"):
            raise CommandError("The webhook URL must end in /telegram/webhook/.")

        try:
            _telegram(token, "setWebhook", {
                "url": url,
                "secret_token": secret,
                "allowed_updates": ["message"],
                "max_connections": 1,
            })
        except AssistantError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS("Telegram webhook registered."))
