from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0040_telegrambotstate_last_webhook_update"),
    ]

    operations = [
        migrations.AddField(
            model_name="telegrambotstate",
            name="conversation_history",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="telegrambotstate",
            name="conversation_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
