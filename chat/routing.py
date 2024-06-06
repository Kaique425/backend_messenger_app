from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path(
        "ws/socket-server/chat/<str:phone_number>",
        consumers.ChatConsumer.as_asgi(),
    ),
    path(
        "ws/socket-server/dashboard/<str:user_id>",
        consumers.AttendancePainelConsumer.as_asgi(),
    ),
]
