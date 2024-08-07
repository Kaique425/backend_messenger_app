# Generated by Django 5.0.3 on 2024-07-06 23:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0006_attendance_last_message_was_sent_by_operator_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="status",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("status_name", models.CharField(max_length=96)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "type",
                    models.CharField(
                        choices=[("Finish", "Finish"), ("Classify", "Classify")],
                        max_length=8,
                    ),
                ),
            ],
        ),
    ]
