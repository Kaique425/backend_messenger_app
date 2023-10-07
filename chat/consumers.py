import json

from asgiref.sync import async_to_sync
from channels.db import DatabaseSyncToAsync
from channels.generic.websocket import WebsocketConsumer

from .models import Message


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        channel_identifier = self.scope["url_route"]["kwargs"]["phone_number"]
        self.room_group_name = channel_identifier
        # self.channel_name = channel_identifier
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )
        self.accept()
        self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": f"You are now connected! this is your channel name {channel_identifier}",
                }
            )
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        sent_by_operator = text_data_json["send_by_operator"]
        if sent_by_operator == False:
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                },
            )

    def chat_message(self, event):
        message = event["message"]
        self.send(
            text_data=json.dumps(
                {
                    "type": "chat",
                    "message": message,
                }
            )
        )

    def notification(self, event):
        message = event["message"]
        self.send(
            text_data=json.dumps(
                {
                    "type": "update_notification",
                    "message": message,
                }
            )
        )
