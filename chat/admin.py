from django.contrib import admin

from .models import Contact, Message, WhatsAppPOST

# Register your models here.


@admin.register(Contact)
class WhatsAppPOSTAdmin(admin.ModelAdmin):
    fields = ("name", "phone", "type")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    fields = (
        "body",
        "status",
        "send_by_operator",
        "whatsapp_message_id",
        "type",
        "media_id",
        "media",
    )


@admin.register(WhatsAppPOST)
class WhatsAppPOSTAdmin(admin.ModelAdmin):
    fields = ("body",)
