import json
import os

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.files.base import ContentFile

from .models import Contact, Message
from .whatsapp_requests import get_media_url


@shared_task
def process_message(notification_data):
    allowed_media_types = getattr(settings, "ALLOWED_MEDIA_TYPES")

    channel_layer = get_channel_layer()

    notification_entry = notification_data["entry"][0]
    notification_changes_value = notification_entry["changes"][0]["value"]

    if "statuses" in notification_changes_value:
        message_statuses = notification_changes_value.get("statuses", [])[0]
        message = Message.objects.filter(
            whatsapp_message_id=message_statuses["id"]
        ).first()
        if message:
            message.status = message_statuses["status"]
            customer_phone_number = message_statuses["recipient_id"]

            channel_name = f"waent_{customer_phone_number}"
            # absolute_media_url = os.environ.get("NGROK_URL").strip("/") + media_url
            json_message = {
                "id": message.id,
                "body": message.body,
                "status": message.status,
                "send_by_operator": message.send_by_operator,
                "created_at": str(message.created_at),
                "type": message.type,
                "contacts": "[27]",
                # "media_url": media_url.replace(
                #     "localhost:5173", os.environ.get("NGROK_URL")
                # )
                # if message.type in allowed_media_types
                # else "",
            }

            if message.context:
                json_message["context"] = message.context.id

            str_json_message = json.dumps(json_message)
            message.save()
            async_to_sync(channel_layer.group_send)(
                channel_name,
                {
                    "type": "notification",
                    "message": str_json_message,
                },
            )

        else:
            print("FAZ NADA")

    else:
        contact_is_already_created = Contact.objects.filter(
            phone=notification_changes_value["contacts"][0]["wa_id"]
        ).exists()

        if contact_is_already_created is False:
            Contact.objects.create(
                name=notification_changes_value["contacts"][0]["profile"]["name"],
                phone=notification_changes_value["contacts"][0]["wa_id"],
            ).save()

        received_message = notification_changes_value["messages"][0]
        message_exists = Message.objects.filter(
            whatsapp_message_id=received_message["id"]
        ).exists()
        if message_exists:
            print(f"JÀ EXISTE")

        else:
            phone_number = notification_changes_value["contacts"][0]["wa_id"]
            channel_name = f"waent_{phone_number}"

            has_context = True if "context" in received_message else False
            if has_context:
                context_whatsapp_message_id = received_message["context"]["id"]
                has_context = Message.objects.filter(
                    whatsapp_message_id=context_whatsapp_message_id
                ).exists()

                if has_context:
                    context_message_instance = Message.objects.filter(
                        whatsapp_message_id=context_whatsapp_message_id
                    ).first()

            if received_message["type"] == "text":
                message = Message.objects.create(
                    whatsapp_message_id=received_message["id"],
                    body=received_message["text"]["body"],
                    type=received_message["type"],
                    origin_identifier=phone_number,
                )

                if has_context:
                    message.context = context_message_instance
                json_message = json.dumps(
                    {
                        "id": message.id,
                        "send_by_operator": message.send_by_operator,
                        "body": message.body,
                        "status": message.status,
                        "created_at": str(message.created_at),
                        "type": message.type,
                        "context": context_message_instance.id if has_context else "",
                    }
                )
                message.save()

            elif received_message["type"] == "contacts":
                message = Message.objects.create(
                    whatsapp_message_id=received_message["id"],
                    type=received_message["type"],
                    origin_identifier=phone_number,
                )

                contact_list = []

                for received_contact in received_message["contacts"]:
                    has_first_name = received_contact["name"].get("first_name", False)
                    if not has_first_name:
                        contact_name = received_contact["name"]["formatted_name"]

                    else:
                        contact_name = received_contact["name"]["first_name"]
                        contact_already_exists = Contact.objects.filter(
                            phone=received_contact["phones"][0]["phone"]
                        ).exists()

                        if contact_already_exists != True:
                            contact = Contact.objects.create(
                                name=contact_name,
                                phone=received_contact["phones"][0]["phone"],
                                type=received_contact["phones"][0]["type"],
                            )
                        contact_list.append(
                            {
                                "name": contact.name,
                                "phone": contact.phone,
                                "type": contact.type,
                            }
                        )
                        contact.save()
                        message.contacts.add(contact)

                json_message = json.dumps(
                    {
                        "contacts": contact_list,
                        "id": message.id,
                        "send_by_operator": message.send_by_operator,
                        "body": message.body if message.body else "",
                        "status": message.status,
                        "type": message.type,
                        "created_at": str(message.created_at),
                    }
                )

            elif received_message["type"] in allowed_media_types:
                current_media_type = received_message["type"]
                message = Message.objects.create(
                    whatsapp_message_id=received_message["id"],
                    media_id=received_message[current_media_type]["id"],
                    type=received_message["type"],
                    origin_identifier=phone_number,
                )
                media_response = get_media_url(message.media_id)

                if received_message[current_media_type].get("caption") is not None:
                    message.body = received_message[current_media_type]["caption"]

                content_file = ContentFile(media_response.content)

                media_content_type = media_response.headers.get("content-type")
                media_type = media_content_type.split("/")[1]
                message.media.save(
                    name=f"{channel_name}_{message.id}.{media_type}",
                    content=content_file,
                    save=False,
                )

                message.save()
                media_url = message.media.url

                absolute_media_url = os.environ.get("NGROK_URL").strip("/") + media_url

                json_message = json.dumps(
                    {
                        "id": message.id,
                        "send_by_operator": message.send_by_operator,
                        "body": message.body if message.body else "",
                        "status": message.status,
                        "media_id": message.media_id,
                        "media_url": absolute_media_url,
                        "type": message.type,
                        "created_at": str(message.created_at),
                    }
                )

                message.save()
            try:
                async_to_sync(channel_layer.group_send)(
                    channel_name,
                    {
                        "type": "chat_message",
                        "message": json_message,
                    },
                )
            except:
                print("Deu erro")
    return print("Message processed!")
