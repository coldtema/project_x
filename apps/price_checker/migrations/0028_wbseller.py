# Generated by Django 5.1.6 on 2025-03-26 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price_checker', '0027_price_price_check_product_31dcaf_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='WBSeller',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Имя продавца WB')),
                ('wb_id', models.CharField(max_length=100, verbose_name='ID продавца WB')),
                ('main_url', models.URLField(blank=True, verbose_name='URL главной страницы')),
                ('catalog_count', models.IntegerField(verbose_name='Всего товаров в каталоге продавца')),
            ],
            options={
                'verbose_name': 'Продавец WB',
                'verbose_name_plural': 'Продавцы WB',
                'indexes': [models.Index(fields=['name'], name='price_check_name_43d0bb_idx')],
            },
        ),
    ]
