# Generated by Django 5.2.3 on 2025-07-11 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_remove_post_time_post_date_alter_post_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='tg_text',
            field=models.CharField(default='', max_length=512, verbose_name='Текст телеграм-уведомления'),
        ),
    ]
