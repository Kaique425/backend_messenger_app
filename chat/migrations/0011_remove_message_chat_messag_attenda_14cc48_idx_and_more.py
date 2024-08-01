# Generated by Django 5.0.3 on 2024-07-12 21:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0010_remove_message_hsm_body_alter_message_hsm_footer_and_more"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="message",
            name="chat_messag_attenda_14cc48_idx",
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(
                fields=["attendance", "created_at"],
                name="chat_messag_attenda_f1f80c_idx",
            ),
        ),
    ]