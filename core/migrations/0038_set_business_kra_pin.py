from django.db import migrations


BUSINESS_KRA_PIN = "P052571280D"


def set_business_kra_pin(apps, schema_editor):
    SiteConfiguration = apps.get_model("core", "SiteConfiguration")
    config = SiteConfiguration.objects.order_by("pk").first()
    if config is None:
        SiteConfiguration.objects.create(kra_pin=BUSINESS_KRA_PIN)
    else:
        SiteConfiguration.objects.filter(pk=config.pk).update(kra_pin=BUSINESS_KRA_PIN)


def clear_business_kra_pin(apps, schema_editor):
    SiteConfiguration = apps.get_model("core", "SiteConfiguration")
    SiteConfiguration.objects.filter(kra_pin=BUSINESS_KRA_PIN).update(kra_pin="")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0037_alter_inventoryitem_description_and_more"),
    ]

    operations = [
        migrations.RunPython(set_business_kra_pin, clear_business_kra_pin),
    ]
