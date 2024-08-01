import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Attendance


@receiver(post_save, sender=Attendance)
def attendance_saved(sender, instance, created, **kwargs):
    print(f"{sender} - {instance} - {created} {kwargs}")
    channel_layer = get_channel_layer()
    channel_name = "1"

    json_message = json.dumps(
        {
            "id": instance.id,
            "is_closed": instance.is_closed,
            "last_message_was_sent_by_operator": instance.last_message_was_sent_by_operator,
            "unread_messages_quantity": instance.unread_messages_quantity,
            "attendance_channel": instance.attendance_channel,
            "customer_phone_number": instance.customer_phone_number,
            "customer_name": instance.customer_name,
            "sector": instance.sector.id,
        }
    )

    async_to_sync(channel_layer.group_send)(
        channel_name,
        {
            "type": "attendance_notification",
            "message": json_message,
        },
    )

    if created:
        print("An Attendance was created")
    else:
        print("An Attendance was updated")
