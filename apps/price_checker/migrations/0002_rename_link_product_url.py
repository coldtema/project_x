# Generated by Django 5.1.6 on 2025-03-03 23:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('price_checker', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='link',
            new_name='url',
        ),
    ]
