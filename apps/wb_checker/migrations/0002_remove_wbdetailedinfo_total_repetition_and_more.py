# Generated by Django 5.1.6 on 2025-05-07 11:55

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wb_checker', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='wbdetailedinfo',
            name='total_repetition',
        ),
        migrations.AddField(
            model_name='wbdetailedinfo',
            name='first_price',
            field=models.IntegerField(default=1, verbose_name='Первая цена продукта WB'),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name='wbdetailedinfo',
            constraint=models.UniqueConstraint(fields=('product', 'latest_price', 'first_price', 'size', 'volume', 'enabled', 'author'), name='total_repetition'),
        ),
    ]
