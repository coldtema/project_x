# Generated by Django 5.1.6 on 2025-03-31 19:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wb_checker', '0009_wbpromotion'),
    ]

    operations = [
        migrations.AddField(
            model_name='wbproduct',
            name='promotion',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='wb_checker.wbpromotion', verbose_name='Промоакция продукта WB'),
        ),
    ]
