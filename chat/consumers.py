import json

from asgiref.sync import async_to_sync
from channels.db import DatabaseSyncToAsync
from channels.generic.websocket import WebsocketConsumer


class AttendancePainelConsumer(WebsocketConsumer):
    def connect(self):
        channel_identifier = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_group_name = channel_identifier

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
    
    def disconnect(self, close_code):

        self.channel_layer.group_discard("group_name", self.channel_name)
        self.close()
        super().disconnect(close_code)

    def attendance_notification(self, event):
        message = event["message"]

        self.send(
            text_data=json.dumps(
                {
                    "type": "attendance_notification",
                    "message": message,
                }
            )
        )


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

    def disconnect(self, close_code):

        self.channel_layer.group_discard("group_name", self.channel_name)
        self.close()
        super().disconnect(close_code)

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
        print(f" MESSAGE NO METODO NOTIFICATION {message}")
        self.send(
            text_data=json.dumps(
                {
                    "type": "update_notification",
                    "message": message,
                }
            )
        )
