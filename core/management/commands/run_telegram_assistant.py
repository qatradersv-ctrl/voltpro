import time

from django.core.management.base import BaseCommand, CommandError

from core.telegram_assistant import AssistantError, poll_once


class Command(BaseCommand):
    help = "Run the private Telegram assistant for quote and invoice workflows."

    def handle(self, *args, **options):
        self.stdout.write("Starting the private VoltPro Telegram assistant. Press Ctrl+C to stop.")
        while True:
            try:
                poll_once()
            except AssistantError as exc:
                if "not configured" in str(exc).lower() or "set groq_api_key" in str(exc).lower() or "set telegram_allowed_user_id" in str(exc).lower():
                    raise CommandError(str(exc)) from exc
                self.stderr.write("Telegram assistant could not reach a provider; retrying in 5 seconds.")
                time.sleep(5)
            except KeyboardInterrupt:
                self.stdout.write("\nTelegram assistant stopped.")
                return
            except Exception:
                # Do not log prompts, client details, provider responses, or credentials.
                self.stderr.write("Telegram assistant encountered an unexpected error; retrying in 5 seconds.")
                time.sleep(5)
