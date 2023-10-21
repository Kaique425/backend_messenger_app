# Generated by Django 4.2.6 on 2023-10-18 21:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0027_message_chat_messag_attenda_14cc48_idx"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="message",
            name="chat_messag_attenda_14cc48_idx",
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(fields=["id"], name="chat_messag_id_db6e10_idx"),
        ),
    ]