# Generated by Django 3.2.14 on 2022-11-02 14:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('videoclases', '0006_rename_school_organizer_schools'),
    ]

    operations = [
        migrations.RenameField(
            model_name='organizer',
            old_name='schools',
            new_name='school',
        ),
    ]
