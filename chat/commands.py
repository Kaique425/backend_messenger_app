import json
from abc import ABC, abstractmethod
from typing import Any

from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import IntegrityError

from core.redis_status_gate import should_enqueue_status

from .models import Contact, HighStructuredMessage, Message
from .utils import get_message_by_wamid, link_message_to_attendance
from .whatsapp_requests import NGROK_URL, get_media_url

STATUS_RANK: dict[str, int] = {
    "queued": 0,
    "sent": 1,
    "delivered": 2,
    "read": 3,
    "failed": 4,
}
TTL_STATUS_SECONDS: int = 60
TTL_MESSAGE_SECONDS: int = 3600


class IWebhookCommand(ABC):
    def __init__(
        self,
        allowed_media_types: set,
        channel_layer: Any,
        notification_value: dict,
    ) -> None:
        self.allowed_media_types = allowed_media_types
        self.channel_layer = channel_layer
        self.value = notification_value

    @abstractmethod
    def execute(self) -> None:
        pass

    def create_base_payload(self, message: Message) -> dict:
        return {
            "id": message.id,
            "send_by_operator": message.send_by_operator,
            "body": message.body or "",
            "status": message.status,
            "type": message.type,
            "created_at": str(message.created_at),
        }

    def ws_send(self, channel_name: str, message_type: str, payload: dict) -> None:
        async_to_sync(self.channel_layer.group_send)(
            channel_name,
            {
                "type": message_type,
                "message": json.dumps(payload),
            },
        )


class TemplateUpdateCommand(IWebhookCommand):
    def execute(self) -> None:
        template = HighStructuredMessage.objects.filter(
            external_template_id=self.value["message_template_id"]
        ).first()

        if template:
            template.language_code = self.value["message_template_name"]
            template.status = self.value["event"]
            template.rejected_reason = self.value.get("reason", "")
            template.name = self.value["message_template_name"]
            template.save()


class StatusUpdateCommand(IWebhookCommand):
    def execute(self) -> None:
        statuses = self.value.get("statuses", [])

        if not statuses:
            return

        status_info: dict = statuses[0]
        new_status: str = status_info["status"]
        wamid: str = status_info["id"]

        ttl: int = getattr(settings, "TTL_STATUS_SECOND", 60)

        if not should_enqueue_status(wamid, new_status, ttl=ttl):
            return

        message = get_message_by_wamid(wamid)
        if not message:
            return

        message.status = status_info["status"]
        message.save()

        customer_phone_number = status_info["recipient_id"]
        channel_name = f"waent_{customer_phone_number}"

        payload: dict = self.create_base_payload(message)
        if message.media:
            payload["media_url"] = NGROK_URL.strip("/") + message.media.url

        self.ws_send(channel_name, "notification", payload)


class ReceiveMessageCommand(IWebhookCommand):
    def execute(self) -> None:
        channel_number = self.value["metadata"]["display_phone_number"]

        wa_id: str = self.value["contacts"][0]["wa_id"]

        try:
            Contact.objects.get_or_create(
                phone=wa_id,
                defaults={"name": self.value["contacts"][0]["profile"]["name"]},
            )
        except IntegrityError:
            pass

        received_message = self.value["messages"][0]
        phone_number = wa_id
        channel_name = f"waent_{phone_number}"

        has_context = "context" in received_message
        context_message_instance = None
        if has_context:
            context_message_instance = Message.objects.filter(
                whatsapp_message_id=received_message["context"]["id"]
            ).first()

        message_type = received_message["type"]

        if message_type == "text":
            message = Message.objects.create(
                whatsapp_message_id=received_message["id"],
                body=received_message["text"]["body"],
                type=message_type,
                origin_identifier=phone_number,
            )
            if has_context:
                message.context = context_message_instance

            link_message_to_attendance(phone_number, message, channel_number)
            message.save()

            payload: dict = self.create_base_payload(message)
            if context_message_instance:
                payload["context"] = context_message_instance.id
            self.ws_send(channel_name, "chat_message", payload)

        elif message_type == "contacts":
            message = Message.objects.create(
                whatsapp_message_id=received_message["id"],
                type=message_type,
                origin_identifier=phone_number,
            )

            contact_list = []
            for rc in received_message["contacts"]:
                has_first_name = rc["name"].get("first_name", False)
                if not has_first_name:
                    contact_name = rc["name"]["formatted_name"]
                else:
                    contact_name = rc["name"]["first_name"]

                contact, _ = Contact.objects.get_or_create(
                    phone=rc["phones"][0]["phone"],
                    defaults={
                        "name": contact_name,
                    },
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

            link_message_to_attendance(phone_number, message, channel_number)
            message.save()

            payload: dict = self.create_base_payload(message)

            if contact_list:
                payload["contacts"] = contact_list

            self.ws_send(channel_name, "chat_message", payload)

        elif message_type in self.allowed_media_types:
            message = Message.objects.create(
                whatsapp_message_id=received_message["id"],
                media_id=received_message[message_type]["id"],
                type=message_type,
                origin_identifier=phone_number,
            )

            media_response = get_media_url(message.media_id)

            if received_message[message_type].get("caption") is not None:
                message.body = received_message[message_type]["caption"]

            content_file = ContentFile(media_response.content)
            media_type = media_response.headers.get("content-type").split("/")[1]
            message.media.save(
                name=f"{channel_name}_{message.id}.{media_type}",
                content=content_file,
                save=False,
            )

            link_message_to_attendance(phone_number, message, channel_number)
            message.save()
            payload: dict = self.create_base_payload(message)

            if message.media:
                payload["media_url"] = NGROK_URL.strip("/") + message.media.url
                payload["media_id"] = message.media_id

            self.ws_send(channel_name, "chat_message", payload)

        elif message_type == "reaction":
            message: Message | None = get_message_by_wamid(
                received_message["reaction"]["message_id"],
            )
            reaction = received_message["reaction"].get("emoji", "")

            if message:
                message.reaction = reaction if reaction else ""
                message.save()

                payload = {
                    "id": message.id,
                    "reaction": message.reaction,
                }
                self.ws_send(channel_name, "notification", payload)


COMMAND_MAP: dict[str, type[IWebhookCommand]] = {
    "message_template_status_update": TemplateUpdateCommand,
    "statuses": StatusUpdateCommand,
    "messages": ReceiveMessageCommand,
}
