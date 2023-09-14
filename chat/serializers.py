from rest_framework import serializers

from .models import Attendance, Buttons, Contact, HighStructuredMessage, Message


class ButtonSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Buttons
        fields = ["id", "body"]


class HighStructuredMessageSerializer(serializers.ModelSerializer):
    buttons = ButtonSerializer(many=True, required=False)

    class Meta:
        model = HighStructuredMessage
        fields = [
            "id",
            "name",
            "body",
            "footer",
            "header",
            "buttons",
            "body_variables_quantity",
            "header_variables_quantity",
            "language_code",
        ]


class MessageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, read_only=True)
    send_by_operator = serializers.BooleanField(default=True)
    status = serializers.CharField(required=False)
    media_url = serializers.FileField(
        source="media", max_length=None, use_url=True, required=False
    )
    contacts = serializers.PrimaryKeyRelatedField(
        allow_empty=True, required=False, many=True, queryset=Contact.objects.all()
    )
    context = serializers.PrimaryKeyRelatedField(
        allow_null=True, required=False, queryset=Message.objects.all()
    )

    class Meta:
        model = Message
        order_by = "created"
        fields = (
            "id",
            "whatsapp_message_id",
            "send_by_operator",
            "body",
            "status",
            "created_at",
            "type",
            "media_id",
            "media_url",
            "contacts",
            "context",
            "origin_identifier",
            "attendance",
        )


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = (
            "id",
            "customer_phone_number",
            "customer_name",
            "created_at",
            "is_closed",
            "closed_at",
        )