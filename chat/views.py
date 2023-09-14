import json
from datetime import datetime

import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.files.base import ContentFile
from django.shortcuts import render
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from .models import Attendance, Contact, HighStructuredMessage, Message, WhatsAppPOST
from .serializers import (
    AttendanceSerializer,
    HighStructuredMessageSerializer,
    MessageSerializer,
)
from .whatsapp_requests import (
    get_media_url,
    send_media_messages,
    send_whatsapp_hsm_message,
    send_whatsapp_message,
)


@api_view(["GET"])
def get_attendance(request):
    print(request.GET)
    attendances = Attendance.objects.filter(is_closed=False)
    serializer = AttendanceSerializer(instance=attendances, many=True)
    return Response(status=200, data=serializer.data)


@api_view(http_method_names=["GET"])
def get_message_history(request, id):
    messages = Message.objects.filter(attendance=id)
    serializer = MessageSerializer(
        instance=messages, many=True, context={"request": request}
    )
    return Response(data=serializer.data)


class MidiaUpload(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        serializer = MessageSerializer(data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            print("IS VALID!!")
            serializer.save()
            print(f"SERIALIZER {serializer.data}")
            data, status_code = send_media_messages(
                file=serializer.data["media_url"],
                caption=serializer.data["body"],
                phone_number=request.data["phone_number"],
            )

            serializer.instance.whatsapp_message_id = data["messages"][0].get("id")

            attendance = Attendance.objects.filter(
                customer_phone_number=request.data["phone_number"]
            ).first()

            serializer.instance.attendance = attendance
            serializer.instance.save()

            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(status=HTTP_400_BAD_REQUEST)


@api_view(http_method_names=("GET", "POST"))
def hsm_view(request):
    if request.method == "GET":
        instances = HighStructuredMessage.objects.all()
        serializer = HighStructuredMessageSerializer(instance=instances, many=True)
        return Response(data=serializer.data, status=HTTP_200_OK)


@api_view(http_method_names=("POST",))
def send_hsm_messages(request):
    data = request.data
    status_code = send_whatsapp_hsm_message(data)

    return Response(status=status_code)


@api_view(["POST"])
def send_message(request):
    data = request.data

    serialized = MessageSerializer(data=data)
    if serialized.is_valid(raise_exception=True):
        message_instance = serialized.save()
        context = data.get("context", False)
        if context:
            context = data.get("context", False)
        status_code, message_data = send_whatsapp_message(
            message_instance.body, data["phone_number"], context
        )
        message_instance.whatsapp_message_id = message_data["messages"][0]["id"]

        message_instance.save()
    return Response(status=status_code, data=serialized.data)


def lobby(request):
    messages = Message.objects.all()
    message_tests = WhatsAppPOST.objects.all()
    context = {"messages": messages, "webhook_messages": message_tests}

    return render(request, "chat/lobby.html", context)


@api_view(["GET", "POST"])
def webhook(request):
    allowed_media_types = getattr(settings, "ALLOWED_MEDIA_TYPES")
    my_token = "teste"
    if request.method == "GET":
        params = request.GET
        hub_mode = params["hub.mode"]
        hub_challenge = params["hub.challenge"]
        hub_verify_token = params["hub.verify_token"]
        if my_token == hub_verify_token:
            return Response(int(hub_challenge), status=HTTP_200_OK)

    if request.method == "POST":
        data = str(request.body)
        messageTeste = WhatsAppPOST.objects.create(body=data)
        notification_data = json.loads(request.body.decode())

        notification_entry = notification_data["entry"][0]

        notification_changes_value = notification_entry["changes"][0]["value"]

        if "statuses" in notification_changes_value:
            message_statuses = notification_changes_value.get("statuses", [])[0]
            message_exists = Message.objects.filter(
                whatsapp_message_id=message_statuses["id"]
            ).exists()
            if message_exists:
                message = Message.objects.get(
                    whatsapp_message_id=message_statuses["id"]
                )
                message.status = message_statuses["status"]
                customer_phone_number = message_statuses["recipient_id"]

                channel_layer = get_channel_layer()
                channel_name = f"waent_{customer_phone_number}"

                json_message = {
                    "id": message.id,
                    "body": message.body,
                    "status": message.status,
                    "send_by_operator": message.send_by_operator,
                    "created_at": str(message.created_at),
                    "type": message.type,
                    "contacts": "[27]",
                    "media_url": request.build_absolute_uri(message.media.url)
                    if message.type in allowed_media_types
                    else "",
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

            if contact_is_already_created == False:
                Contact.objects.create(
                    name=notification_changes_value["contacts"][0]["profile"]["name"],
                    phone=notification_changes_value["contacts"][0]["wa_id"],
                ).save()

            channel_layer = get_channel_layer()

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
                            "context": context_message_instance.id
                            if has_context
                            else "",
                        }
                    )
                    message.save()

                elif received_message["type"] == "contacts":
                    print("UM novo contato")
                    message = Message.objects.create(
                        whatsapp_message_id=received_message["id"],
                        type=received_message["type"],
                        origin_identifier=phone_number,
                    )

                    contact_list = []
                    teste = received_message["contacts"]
                    print(f"RECEIVED CONTACTS {teste}")

                    for received_contact in received_message["contacts"]:
                        has_first_name = received_contact["name"].get(
                            "first_name", False
                        )
                        if not has_first_name:
                            contact_name = received_contact["name"]["formatted_name"]

                        else:
                            print("Tem first name")
                            contact_name = received_contact["name"]["first_name"]
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

                    print(f"CONTACT LIST {contact_list}")

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
                    media_url = request.build_absolute_uri(message.media.url)
                    json_message = json.dumps(
                        {
                            "id": message.id,
                            "send_by_operator": message.send_by_operator,
                            "body": message.body if message.body else "",
                            "status": message.status,
                            "media_id": message.media_id,
                            "media_url": media_url,
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

        return Response(status=HTTP_200_OK)