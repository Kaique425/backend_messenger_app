from rest_framework import serializers

from .models import Contact, Message


class MessageSerializer(serializers.ModelSerializer):
    media = serializers.FileField(max_length=None, use_url=True)
    id = serializers.IntegerField(required=False)
    send_by_operator = serializers.BooleanField(default=True)
    status = serializers.CharField(required=False)
    media = serializers.FileField(max_length=None, use_url=True, required=False)
    contacts = serializers.PrimaryKeyRelatedField(
        allow_empty=False, required=False, many=True, queryset=Contact.objects.all()
    )

    # def get_id(self, obj):
    #     # Aqui você pode definir a lógica para retornar o ID do objeto, se necessário
    #     return obj.id if obj.id else None

    class Meta:
        model = Message
        fields = (
            "id",
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
