# Generated by Django 5.1.6 on 2025-03-16 13:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('price_checker', '0008_product_categoty_deletedprice_deletedproduct'),
    ]

    operations = [
        migrations.RenameField(
            model_name='deletedproduct',
            old_name='categoty',
            new_name='category',
        ),
        migrations.RenameField(
            model_name='product',
            old_name='categoty',
            new_name='category',
        ),
    ]
