import json

from django.core.cache import cache
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from chat.utils import link_message_to_attendance

from .filters import ContactFilter
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
    ContactSerializer,
    DynamicMessageSerializer,
    HighStructuredMessageSerializer,
    MessageSerializer,
    SectorSerializer,
    TemplateMessageSerializer,
)
from .task import process_message
from .whatsapp_requests import (
    create_template_message,
    send_media_messages,
    send_whatsapp_hsm_message,
    send_whatsapp_message,
)


class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ContactFilter


class SectorViewSet(ModelViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer

    def list(self, request, *args, **kwargs):

        sector_list = cache.get("sector_list")

        if sector_list is None:
            sectors = self.get_queryset()
            sector_list = self.get_serializer(sectors, many=True).data

            cache.set("sector_list", sector_list, timeout=3600)

        return Response(sector_list)


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


class AttendanceDetailAPIView(ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer

    def list(self, request, *args, **kwargs):
        queryset = Attendance.objects.filter(is_closed=False)
        serializer = self.get_serializer(queryset, many=True)

        return Response(status=200, data=serializer.data)

    def partial_update(self, request, *args, **kwargs):
        attendance = self.get_object()
        serializer = self.get_serializer(
            instance=attendance,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response(data=serializer.data, status=HTTP_200_OK)

    @action(detail=True, methods=["patch"])
    def finish(self, request, *args, **kwargs):
        attendance = self.get_object()
        attendance.is_closed = True
        attendance.closed_at = now()
        attendance.save()
        return Response(status=HTTP_200_OK)


class HistoryMessageListAPIView(APIView):
    def get(self, request, id):
        messages = Message.objects.filter(attendance=id).prefetch_related("contacts")
        serializer = DynamicMessageSerializer(
            instance=messages, many=True, context={"request": request}
        )
        return Response(data=serializer.data)


class HsmAPIView(APIView):

    def post(self, request):
        data = request.data
        hsm_component_list = [component for component in data.values()]

        template = {
            "name": data["title"]["text"],
            "category": "MARKETING",
            "allow_category_change": True,
            "language": "pt_BR",
            "components": hsm_component_list,
        }

        response = create_template_message(template)

        return Response(data=template)

    def get(self, request):
        instances = HighStructuredMessage.objects.prefetch_related("buttons")
        serializer = HighStructuredMessageSerializer(instance=instances, many=True)

        return Response(data=serializer.data, status=HTTP_200_OK)


class MidiaUploadAPIView(APIView):
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

            message_instance = serializer.instance
            phone_number = request.data["phone_number"]

            link_message_to_attendance(phone_number, message_instance, "15550947876")

            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(status=HTTP_400_BAD_REQUEST)


class SendHsmMessageAPIView(APIView):

    def post(self, request):
        request.data["type"] = "hsm"
        phone_number = request.data["phone_number"]

        serialized = TemplateMessageSerializer(data=request.data)
        serialized.is_valid(raise_exception=True)

        try:
            status_code, message_data = send_whatsapp_hsm_message(request.data)
            whatsapp_message_id = message_data["messages"][0]["id"]
            message_instance = serialized.save(whatsapp_message_id=whatsapp_message_id)
            link_message_to_attendance(phone_number, message_instance, "15550947876")

            return Response(data=message_data, status=status_code)

        except Exception as e:

            return Response({"Error": str(e)}, status=HTTP_400_BAD_REQUEST)


class SendMessageAPIView(APIView):
    def post(self, request):
        serialized = MessageSerializer(data=request.data)
        serialized.is_valid(raise_exception=True)

        message_body = request.data["body"]
        context = request.data.get("context", "")
        phone_number = request.data["phone_number"]

        try:
            status_code, message_data = send_whatsapp_message(
                message_body, phone_number, context
            )
            whatsapp_message_id = message_data["messages"][0]["id"]

            message_instance = serialized.save(whatsapp_message_id=whatsapp_message_id)
            link_message_to_attendance(phone_number, message_instance, "15550947876")
            return Response(status=status_code, data=serialized.data)

        except Exception as e:

            return Response({"Error": str(e)}, status=HTTP_400_BAD_REQUEST)


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
