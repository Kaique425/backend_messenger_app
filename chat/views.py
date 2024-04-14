import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import (
    Attendance,
    Contact,
    HighStructuredMessage,
    Message,
    Sector,
    WabaChannel,
    WhatsAppPOST,
)
from .serializers import (
    AttendanceSerializer,
    HighStructuredMessageSerializer,
    MessageSerializer,
    SectorSerializer,
)
from .task import process_message
from .whatsapp_requests import (
    get_media_url,
    send_media_messages,
    send_whatsapp_hsm_message,
    send_whatsapp_message,
)


class SectorViewSet(ModelViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    # pagination_class = PageNumberPagination


class ChannelsViewSet(APIView):
    def get(self, request):
        channels = WabaChannel.objects.all()
        channels_list = channels.values(
            "channel_external_id",
            "channel_name",
            "channel_phone",
            "created_at",
            "default_sector",
            "default_sector_id",
            "id",
            "updated_at",
        )
        return Response(channels_list)


class AttendanceListAPIView(APIView):
    def get(self, request):
        attendances = Attendance.objects.filter(is_closed=False)
        serializer = AttendanceSerializer(instance=attendances, many=True)
        return Response(status=200, data=serializer.data)


class AttendanceDetailAPIView(APIView):
    def get_attendance(self, pk):
        attendance = get_object_or_404(
            Attendance.objects.filter(is_closed=False), pk=pk
        )
        return attendance

    def get(self, request, pk):
        attendance = self.get_attendance(pk=pk)
        serializer = AttendanceSerializer(instance=attendance, many=False)
        return Response(status=200, data=serializer.data)

    def patch(self, request, pk):
        attendance = self.get_attendance(pk=pk)
        serializer = AttendanceSerializer(
            instance=attendance, data=request.data, partial=True
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(data=serializer.data, status=HTTP_200_OK)


class HistoryMessageListAPIView(APIView):
    def get(self, request, id):
        messages = Message.objects.filter(attendance=id).prefetch_related("contacts")
        serializer = MessageSerializer(
            instance=messages, many=True, context={"request": request}
        )
        return Response(data=serializer.data)


class MidiaUpload(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        serializer = MessageSerializer(data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            media_file = request.data.get("media_url")
            if media_file:
                serializer.validated_data["media"] = media_file
            serializer.save()

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
        instances = HighStructuredMessage.objects.prefetch_related("buttons")
        serializer = HighStructuredMessageSerializer(instance=instances, many=True)
        return Response(data=serializer.data, status=HTTP_200_OK)


@api_view(http_method_names=("POST",))
def send_hsm_messages(request):
    data = request.data
    status_code, response = send_whatsapp_hsm_message(data)

    return Response(data=response.json(), status=status_code)


@api_view(["POST"])
def send_message(request):
    data = request.data

    serialized = MessageSerializer(data=data)
    if serialized.is_valid(raise_exception=True):
        context = data.get("context", False)
        if context:
            context = data.get("context", False)
        status_code, message_data = send_whatsapp_message(
            data["body"], data["phone_number"], context
        )
        print(f"STATUS ==> {status_code} CONTENT {message_data}")
        try:
            whatsapp_message_id = message_data["messages"][0]["id"]
        except:
            whatsapp_message_id = ""
        message_instance = serialized.save(
            whatsapp_message_id=whatsapp_message_id,
        )

        message_instance.save()
    return Response(status=status_code, data=serialized.data)


class Webhook(APIView):
    def get(self, request):
        my_token = "teste"
        params = request.GET
        hub_challenge = params["hub.challenge"]
        hub_verify_token = params["hub.verify_token"]
        if my_token == hub_verify_token:
            return Response(int(hub_challenge), status=HTTP_200_OK)

    def post(self, request):
        data = str(request.body)
        WhatsAppPOST.objects.create(body=data)
        notification_data = json.loads(request.body.decode())
        process_message.delay(notification_data)

        return Response(status=HTTP_200_OK)
