from django.contrib import admin

from .models import (
    Attendance,
    Button,
    Contact,
    HighStructuredMessage,
    Message,
    Sector,
    Status,
    WabaChannel,
    WhatsAppPOST,
)


# Register your models here.
@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "type",
        "created_at",
        "updated_at",
        "status_name",
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    readonly_fields = ["created_at", "updated_at", "id"]
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


@admin.register(Button)
class ButtonAdmin(admin.ModelAdmin):
    fields = ("body",)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "name",
        "phone",
        "type",
        "created_at",
        "updated_at",
    )


@admin.register(WhatsAppPOST)
class WhatsAppPOSTAdmin(admin.ModelAdmin):
    fields = ("body",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    readonly_fields = [
        "created_at",
    ]
    ordering = ("-created_at",)
    fields = (
        "body",
        "status",
        "reaction",
        "send_by_operator",
        "whatsapp_message_id",
        "type",
        "media_id",
        "media",
        "context",
        "origin_identifier",
        "attendance",
        "failed_reason",
        "hsm_footer",
        "hsm_header",
        "hsm_buttons",
        "created_at",
    )


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
        "external_template_id",
        "category",
        "rejected_reason",
        "status",
    )


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    fields = ("name",)


@admin.register(WabaChannel)
class WabaChannelAdmin(admin.ModelAdmin):
    readonly_fields = ["created_at", "updated_at"]
    fields = (
        "channel_name",
        "default_sector",
        "channel_phone",
        "channel_external_id",
        "created_at",
        "updated_at",
    )
