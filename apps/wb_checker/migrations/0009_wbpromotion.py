# Generated by Django 5.1.6 on 2025-03-31 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wb_checker', '0008_alter_wbbrand_wb_id_alter_wbseller_wb_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='WBPromotion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Имя промоакции WB')),
                ('wb_id', models.IntegerField(verbose_name='ID промоации WB')),
                ('main_url', models.URLField(blank=True, verbose_name='URL страницы промоакции')),
                ('shard_key', models.CharField(max_length=200, verbose_name='Часть url для достука к api промоакции WB')),
                ('query', models.CharField(max_length=200, verbose_name='Параметр для передачи в api промоакции WB')),
            ],
            options={
                'verbose_name': 'Промоакция',
                'verbose_name_plural': 'Промоакции',
                'indexes': [models.Index(fields=['wb_id'], name='wb_checker__wb_id_f23220_idx')],
            },
        ),
    ]
