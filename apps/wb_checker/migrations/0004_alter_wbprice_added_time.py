# Generated by Django 5.1.6 on 2025-03-26 22:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wb_checker', '0003_remove_wbbrand_catalog_count_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wbprice',
            name='added_time',
            field=models.DateTimeField(verbose_name='Добавлено'),
        ),
    ]
