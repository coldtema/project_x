# Generated by Django 5.1.6 on 2025-04-02 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wb_checker', '0011_alter_wbproduct_artikul_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wbproduct',
            name='artikul',
            field=models.IntegerField(unique=True, verbose_name='Артикул продукта WB'),
        ),
    ]
