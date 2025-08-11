from rest_framework import serializers

from .models import (
    Attendance,
    Button,
    Contact,
    HighStructuredMessage,
    Message,
    Sector,
    WhatsAppPOST,
)


class WhatsAppPOSTSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppPOST
        fields = ("body",)


class ContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contact
        fields = (
            "name",
            "phone",
            "type",
            "created_at",
            "updated_at",
        )

    def validate_phone(self, value):
        if Contact.objects.filter().exists():
            raise serializers.ValidationError(
                code="unique", detail="This contact with phone number already exists."
            )
        return value


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = (
            "id",
            "name",
            "created_at",
            "updated_at",
        )


class ButtonSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Button
        fields = [
            "id",
            "body",
            "created_at",
            "updated_at",
        ]


class HighStructuredMessageSerializer(serializers.ModelSerializer):
    buttons = ButtonSerializer(many=True, required=False)

    class Meta:
        model = HighStructuredMessage
        fields = [
            "id",
            "category",
            "status",
            "name",
            "body",
            "footer",
            "header",
            "buttons",
            "body_variables_quantity",
            "header_variables_quantity",
            "created_at",
            "updated_at",
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
    whatsapp_message_id = serializers.CharField(required=False)

    class Meta:
        model = Message
        order_by = "created"
        fields = (
            "id",
            "reaction",
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
            "failed_reason",
        )


class DynamicMessageSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        if instance.type == "hsm":
            serializer = TemplateMessageSerializer(instance, context=self.context)
        else:
            serializer = MessageSerializer(instance, context=self.context)
        return serializer.data


class TemplateMessageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, read_only=True)
    send_by_operator = serializers.BooleanField(default=True)
    status = serializers.CharField(required=False)
    media_url = serializers.FileField(
        source="media", max_length=None, use_url=True, required=False
    )
    whatsapp_message_id = serializers.CharField(required=False)

    class Meta:
        model = Message
        order_by = "created"
        fields = (
            "id",
            "reaction",
            "whatsapp_message_id",
            "send_by_operator",
            "body",
            "status",
            "created_at",
            "type",
            "media_id",
            "media_url",
            "attendance",
            "failed_reason",
            "hsm_footer",
            "hsm_header",
            "hsm_buttons",
        )


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = (
            "id",
            "last_message_was_sent_by_operator",
            "unread_messages_quantity",
            "attendance_channel",
            "customer_phone_number",
            "customer_name",
            "created_at",
            "is_closed",
            "closed_at",
            "sector",
        )
