# Generated by Django 5.1.6 on 2025-04-02 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0018_rename_dest_author_dest_id_author_dest_name'),
        ('wb_checker', '0010_wbproduct_promotion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wbproduct',
            name='artikul',
            field=models.IntegerField(verbose_name='Артикул продукта WB'),
        ),
        migrations.AddIndex(
            model_name='wbproduct',
            index=models.Index(fields=['artikul'], name='wb_checker__artikul_25d386_idx'),
        ),
    ]
