from django.urls import path

from . import views

urlpatterns = [
    path("", views.lobby, name="lobby"),
    path("webhook", views.webhook, name="webhook"),
    path("send_message", views.send_message, name="send_message"),
    path("upload_midia", views.MidiaUpload.as_view(), name="midia_upload"),
]
