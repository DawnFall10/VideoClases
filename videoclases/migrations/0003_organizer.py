# Generated by Django 3.2.14 on 2022-10-26 19:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('videoclases', '0002_alter_course_year'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organizer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('changed_password', models.BooleanField(default=True)),
                ('courses', models.ManyToManyField(blank=True, to='videoclases.Course')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='videoclases.school')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Organizador',
                'verbose_name_plural': 'Organizadores',
            },
        ),
    ]
