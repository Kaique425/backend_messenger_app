from django.urls import path

from . import views

urlpatterns = [
    path("", views.lobby, name="lobby"),
    path("webhook", views.webhook, name="webhook"),
    path("send_message", views.send_message, name="send_message"),
    path("upload_midia", views.MidiaUpload.as_view(), name="midia_upload"),
    path("hsm", views.hsm_view, name="hsm"),
    path("send_hsm_message", views.send_hsm_messages, name="send_hsm"),
    path(
        "get_attendance",
        views.get_attendance,
        name="get_messages",
    ),
    path("messagehistory/<int:id>", views.get_message_history, name="messagehistory"),
]
