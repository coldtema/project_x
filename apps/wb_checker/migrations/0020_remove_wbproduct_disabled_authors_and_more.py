# Generated by Django 5.1.6 on 2025-04-07 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0019_author_slots'),
        ('wb_checker', '0019_remove_wbproduct_enabled'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wbproduct',
            name='disabled_authors',
        ),
        migrations.RemoveField(
            model_name='wbproduct',
            name='enabled_authors',
        ),
        migrations.AddField(
            model_name='wbproduct',
            name='disabled_connection',
            field=models.ManyToManyField(related_name='disabled_connection', to='blog.author', verbose_name='Связь (нет в наличии)'),
        ),
        migrations.AddField(
            model_name='wbproduct',
            name='enabled_connection',
            field=models.ManyToManyField(related_name='enabled_connection', to='blog.author', verbose_name='Связь (есть в наличии)'),
        ),
    ]
