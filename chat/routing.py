from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/socket-server/<str:phone_number>", consumers.ChatConsumer.as_asgi())
]
