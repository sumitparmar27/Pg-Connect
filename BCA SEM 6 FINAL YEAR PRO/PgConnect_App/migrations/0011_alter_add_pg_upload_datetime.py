# Generated by Django 5.1.5 on 2025-02-17 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PgConnect_App', '0010_add_pg_upload_datetime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='add_pg',
            name='upload_datetime',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
