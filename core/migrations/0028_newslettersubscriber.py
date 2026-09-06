# Generated migration for NewsletterSubscriber model

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_alter_blogpost_id_alter_inventoryitem_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsletterSubscriber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(help_text='Subscriber email address', max_length=254, unique=True)),
                ('name', models.CharField(blank=True, help_text='Subscriber name (optional)', max_length=100)),
                ('is_active', models.BooleanField(default=True, help_text='Whether the subscription is active')),
                ('subscribed_at', models.DateTimeField(auto_now_add=True)),
                ('unsubscribed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Newsletter Subscriber',
                'verbose_name_plural': 'Newsletter Subscribers',
                'ordering': ['-subscribed_at'],
            },
        ),
    ]