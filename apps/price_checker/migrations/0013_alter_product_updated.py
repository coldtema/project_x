# Generated by Django 5.1.6 on 2025-03-18 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price_checker', '0012_alter_product_options_product_created_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='updated',
            field=models.DateTimeField(),
        ),
    ]
