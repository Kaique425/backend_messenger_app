# Generated by Django 5.0.3 on 2024-07-13 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0013_remove_attendance_reaction_message_reaction"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="failed_reason",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
