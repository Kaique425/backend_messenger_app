from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Status(models.Model):

    STATUS_CHOICES = (("Finish", "Finish"), ("Classify", "Classify"))

    status_name = models.CharField(max_length=96)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    type = models.CharField(max_length=8, choices=STATUS_CHOICES)

    def save(self, *args, **kwargs):
        if self.type not in dict(self.STATUS_CHOICES).keys():
            raise ValueError("The specified status type is not in allowed types!")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.status_name


class Sector(models.Model):
    name = models.CharField(max_length=54)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Button(models.Model):
    body = models.CharField(max_length=96)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.body}"


class HighStructuredMessage(models.Model):

    STATUS_CHOICES = (
        ("pending", "PENDING"),
        ("rejected", "REJECTED"),
        ("approved", "APPROVED"),
        ("disabled", "DISABLED"),
        ("paused", "PAUSED"),
    )

    CATEGORY_CHOICES = (
        ("marketing", "MARKETING"),
        ("utility", "UTILITY"),
        ("authentication", " AUTHENTICATION"),
    )

    name = models.CharField(
        max_length=512,
    )
    body = models.TextField(
        max_length=1052,
    )
    external_template_id = models.CharField(max_length=16, null=True, blank=True)
    category = models.CharField(
        max_length=14, choices=CATEGORY_CHOICES, default="marketing"
    )
    rejected_reason = models.CharField(max_length=96, default="")
    status = models.CharField(max_length=14, choices=STATUS_CHOICES, default="pending")
    header = models.CharField(max_length=256, null=True, blank=True)
    footer = models.CharField(max_length=256, null=True, blank=True)
    buttons = models.ManyToManyField(to=Button, blank=True)
    header_variables_quantity = models.IntegerField(default=0)
    body_variables_quantity = models.IntegerField(default=0)
    language_code = models.CharField(max_length=5, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class WhatsAppPOST(models.Model):
    body = models.CharField(max_length=4000)


class Contact(models.Model):
    name = models.CharField(max_length=96, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Attendance(models.Model):
    last_message_was_sent_by_operator = models.BooleanField(null=True, blank=True)
    unread_messages_quantity = models.IntegerField(default=0)
    customer_phone_number = models.CharField(max_length=13)
    customer_name = models.CharField(max_length=64, blank=True, null=True)
    attendance_channel = models.CharField(max_length=13, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    sector = models.ForeignKey(
        Sector, on_delete=models.DO_NOTHING, blank=True, null=True
    )

    def finish_attendance(self):
        self.is_close = True
        self.closed_at = timezone.now()
        self.save()

    def __str__(self):
        attendance_status = "FINALIZADO" if self.is_closed else "EM ABERTO"
        return f"{self.customer_name} - {self.customer_phone_number} - {self.id} {attendance_status}"


class Message(models.Model):
    class Meta:
        ordering = [
            "created_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "attendance",
                    "created_at",
                ]
            )
        ]

    reaction = models.CharField(max_length=16, null=True, blank=True)
    whatsapp_message_id = models.CharField(max_length=128)
    send_by_operator = models.BooleanField(default=False)
    body = models.TextField(max_length=4096, blank=True, null=True)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    type = models.CharField(max_length=24, blank=True, null=True)
    media_id = models.CharField(max_length=255, blank=True, null=True)
    media = models.FileField(upload_to="media", blank=True, null=True)
    contacts = models.ManyToManyField(Contact, "contacts", blank=True)
    context = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True
    )
    origin_identifier = models.CharField(max_length=13, blank=True, null=True)
    failed_reason = models.CharField(max_length=128, null=True, blank=True)
    attendance = models.ForeignKey(
        Attendance,
        related_name="messages",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    hsm_footer = models.CharField(max_length=60, blank=True, null=True, default="")
    hsm_header = models.CharField(max_length=60, blank=True, null=True, default="")
    hsm_buttons = ArrayField(
        models.CharField(max_length=25), blank=True, null=True, size=8
    )

    def __str__(self):
        return f"ID:{self.id} --> {self.body} enviada em {self.created_at}"


class WabaChannel(models.Model):
    class Meta:
        ordering = [
            "created_at",
        ]

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    channel_name = models.CharField(max_length=64)
    channel_phone = models.CharField(max_length=13, unique=True)
    channel_external_id = models.CharField(max_length=15, unique=True)
    default_sector = models.ForeignKey(
        Sector, related_name="default_sector", on_delete=models.PROTECT
    )

    def __str__(self):

        return f"{self.id} - {self.channel_name} - {self.channel_phone}"
