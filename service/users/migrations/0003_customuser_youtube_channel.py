# Generated by Django 4.2.11 on 2024-05-06 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_customuser_options_alter_customuser_managers_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='youtube_channel',
            field=models.URLField(blank=True, null=True),
        ),
    ]