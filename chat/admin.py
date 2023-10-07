from django.contrib import admin

from .models import (
    Attendance,
    Buttons,
    Contact,
    HighStructuredMessage,
    Message,
    WhatsAppPOST,
)

# Register your models here.


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    fields = (
        "customer_phone_number",
        "customer_name",
        "is_closed",
        "closed_at",
        "sector",
    )


@admin.register(Buttons)
class ButtonsAdmin(admin.ModelAdmin):
    fields = ("body",)


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
        "context",
        "origin_identifier",
        "attendance",
    )


@admin.register(WhatsAppPOST)
class WhatsAppPOSTAdmin(admin.ModelAdmin):
    fields = ("body",)


@admin.register(HighStructuredMessage)
class HighStructuredMessageAdmin(admin.ModelAdmin):
    fields = (
        "name",
        "body",
        "header",
        "footer",
        "buttons",
        "body_variables_quantity",
        "header_variables_quantity",
        "language_code",
    )
