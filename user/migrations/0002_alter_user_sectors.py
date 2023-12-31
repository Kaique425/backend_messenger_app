# Generated by Django 4.2.6 on 2023-11-04 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0001_initial"),
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="sectors",
            field=models.ManyToManyField(
                blank=True, related_name="user_sector", to="chat.sector"
            ),
        ),
    ]
