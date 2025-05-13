from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wb_checker', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE UNIQUE INDEX source_repetition_2
            ON wb_checker_topwbproduct (artikul, source, menu_category_id)
            NULLS NOT DISTINCT;
            """
        )
    ]
