from django.db import models, transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone


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
    name = models.CharField(
        max_length=512,
    )
    body = models.TextField(
        max_length=1052,
    )
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
    customer_phone_number = models.CharField(max_length=13)
    customer_name = models.CharField(max_length=64, blank=True, null=True)
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
        return f"{self.customer_name} - {self.customer_phone_number} - {self.id}"


class Message(models.Model):
    class Meta:
        ordering = [
            "created_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "attendance",
                ]
            )
        ]

    whatsapp_message_id = models.CharField(max_length=128, default="")
    send_by_operator = models.BooleanField(default=False)
    body = models.TextField(max_length=4096, blank=True, null=True)
    status = models.CharField(
        max_length=20,
    )
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    type = models.CharField(max_length=24, blank=True, null=True)
    media_id = models.CharField(max_length=255, blank=True, null=True)
    media = models.FileField(upload_to="media", blank=True, null=True)
    contacts = models.ManyToManyField(Contact, "contacts", blank=True)
    context = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True
    )
    origin_identifier = models.CharField(max_length=13, blank=True, null=True)
    attendance = models.ForeignKey(
        Attendance,
        related_name="messages",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"ID:{self.id} --> {self.body} enviada em {self.created_at}"


@transaction.atomic
@receiver(pre_save, sender=Message)
def link_message_to_last_open_attendance(sender, instance, **kwargs):
    phone_number = instance.origin_identifier
    try:
        last_open_attendance = Attendance.objects.get(
            customer_phone_number=phone_number, is_closed=False
        )
        instance.attendance = last_open_attendance
        print(f"INSTANCIA --> {instance} FILTERED ATTENDANCE {last_open_attendance}")
    except Attendance.DoesNotExist:
        contact_info = Contact.objects.get(phone=phone_number)
        print(f"CONTACT INFO {contact_info}")
        new_attendance = Attendance.objects.create(
            customer_phone_number=contact_info.phone,
            customer_name=contact_info.name,
        )
        instance.attendance = new_attendance
        print(f"INSTANCIA --> {instance} FILTERED ATTENDANCE {new_attendance}")
