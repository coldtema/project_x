# Generated by Django 5.1.6 on 2025-04-08 21:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wb_checker', '0021_remove_wbproduct_promotion_delete_wbpromotion'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='wbproduct',
            options={'verbose_name': 'Продукт WB', 'verbose_name_plural': 'Продукты WB'},
        ),
        migrations.RemoveField(
            model_name='wbproduct',
            name='created',
        ),
        migrations.RemoveField(
            model_name='wbproduct',
            name='disabled_connection',
        ),
        migrations.RemoveField(
            model_name='wbproduct',
            name='enabled_connection',
        ),
        migrations.RemoveField(
            model_name='wbproduct',
            name='latest_price',
        ),
        migrations.RemoveField(
            model_name='wbproduct',
            name='updated',
        ),
    ]
