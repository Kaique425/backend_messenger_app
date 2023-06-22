from django.db import models


class WhatsAppPOST(models.Model):
    body = models.CharField(max_length=564)


class Contact(models.Model):
    name = models.CharField(max_length=96, blank=True, null=True)
    phone = models.CharField(max_length=20)
    type = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Message(models.Model):
    whatsapp_message_id = models.CharField(max_length=264, default="")
    send_by_operator = models.BooleanField(default=False)
    body = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
    )
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    type = models.CharField(max_length=24, blank=True, null=True)
    media_id = models.CharField(max_length=255, blank=True, null=True)
    media = models.FileField(upload_to="media", blank=True, null=True)
    contacts = models.ManyToManyField(Contact, "contacts")

    def __str__(self):
        return f"{self.body} enviada em {self.created_at}"


class Attendance(models.Model):
    customer_phone_number = models.CharField(max_length=13)
    customer_name = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    messages = models.ManyToManyField(Message)
