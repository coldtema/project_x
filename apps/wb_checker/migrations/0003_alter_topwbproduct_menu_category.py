# Generated by Django 5.1.6 on 2025-05-13 23:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wb_checker', '0002_custom_constraint'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topwbproduct',
            name='menu_category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='wb_checker.wbmenucategory', verbose_name='Категория продукта WB'),
            preserve_default=False,
        ),
    ]
