# Generated by Django 5.2.3 on 2025-06-20 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_alter_subrequest_duration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subrequest',
            name='status',
            field=models.CharField(choices=[('FINISHED', 'FINISHED'), ('ACCEPTED', 'ACCEPTED'), ('SENT', 'SENT'), ('PENDING', 'PENDING'), ('DECLINED', 'DECLINED')], default='PENDING', max_length=8),
        ),
    ]
