# Generated by Django 5.1.6 on 2025-03-26 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wb_checker', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='wbbrand',
            name='full_control',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='wbseller',
            name='full_control',
            field=models.BooleanField(default=False),
        ),
    ]
