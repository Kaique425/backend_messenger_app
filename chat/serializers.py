from rest_framework import serializers

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    media = serializers.FileField(max_length=None, use_url=True)

    class Meta:
        model = Message
        fields = (
            "whatsapp_message_id",
            "send_by_operator",
            "body",
            "status",
            "created_at",
            "type",
            "media_id",
            "media",
            "contacts",
        )
