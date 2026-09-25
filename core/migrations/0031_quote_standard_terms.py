from django.db import migrations, models

LEGACY_TERMS = (
    "50% deposit on acceptance, balance on completion. Quote valid for 30 days "
    "from issue date unless stated otherwise. Materials sourced to spec unless "
    "an alternative is agreed in writing."
)

STANDARD_TERMS = """Quote valid for 30 days.
50% deposit required before work begins; balance on completion.
Additional work/materials are charged separately.
Prices may change if scope or material costs change.
Warranty covers agreed workmanship and manufacturer terms only.
Customer must provide access to the work site.
Delays beyond VoltPro\u2019s control are not our responsibility.
Cancellation after work/material procurement may attract charges.
By approving the quote or paying the deposit, the customer accepts these terms.
Terms governed by the laws of Kenya."""


def apply_standard_terms(apps, schema_editor):
    Quote = apps.get_model("core", "Quote")
    Quote.objects.filter(models.Q(terms="") | models.Q(terms=LEGACY_TERMS)).update(terms=STANDARD_TERMS)


def revert_standard_terms(apps, schema_editor):
    Quote = apps.get_model("core", "Quote")
    Quote.objects.filter(terms=STANDARD_TERMS).update(terms=LEGACY_TERMS)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_alter_blogpost_featured_image_alter_project_image_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quote',
            name='terms',
            field=models.TextField(blank=True, default=STANDARD_TERMS, help_text='One condition per line; rendered as a numbered list on the quote and its PDF. Leave blank to print the VoltPro standard terms.'),
        ),
        migrations.RunPython(apply_standard_terms, revert_standard_terms),
    ]
