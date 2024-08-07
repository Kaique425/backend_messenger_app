# Generated by Django 5.0.3 on 2024-07-18 23:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0017_alter_highstructuredmessage_category_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="highstructuredmessage",
            name="category",
            field=models.CharField(
                choices=[
                    ("marketing", "MARKETING"),
                    ("utility", "UTILITY"),
                    ("authentication", " AUTHENTICATION"),
                ],
                default="marketing",
                max_length=14,
            ),
        ),
    ]
