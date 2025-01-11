import os

import requests
from django.core.exceptions import ObjectDoesNotExist
from dotenv import load_dotenv

from .models import Message, WhatsAppPOST

enviroment = load_dotenv()

send_message_url = "https://graph.facebook.com/v20.0/101917902878484/messages"

template_creation_url = (
    "https://graph.facebook.com/v20.0/101917902878484/message_templates"
)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.getenv('WHATSAPP_PERMANENT_TOKEN')}",
}

DEBUG = True
NGROK_URL = os.getenv("NGROK_URL")
API_VERSION = os.getenv("WHATSAPP_API_VERSION")


def create_template_message(template_info):
    with requests.post(
        template_creation_url, headers=headers, json=template_info
    ) as response:
        return response


def save_media_message():
    return True


def send_media_messages(file, caption, phone_number):
    new_file_link = file.replace("http://localhost:8000", NGROK_URL)
    json = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "image",
        "image": {"link": new_file_link, "caption": caption},
    }
    response = requests.post(url=send_message_url, headers=headers, json=json)

    data = response.json()
    return data, response.status_code


def get_media_url(media_id):
    try:
        url = f"https://graph.facebook.com/v16.0/{media_id}/"
        response = requests.get(url, headers=headers)
        data = response.json()

        status_code = response.status_code
        media_url = data["url"]

        media_response = requests.get(media_url, headers=headers)
        return media_response
    except:
        print(f"Error status code {status_code}")


def send_whatsapp_hsm_message(data):
    components = data["components"]

    mounteds_components = []
    for component in components:

        mountedComponent = {
            "type": component["type"],
            "parameters": [
                {"type": "text", "text": value} for value in component["values"]
            ],
        }
        mounteds_components.append(mountedComponent)

    json = {
        "messaging_product": "whatsapp",
        "to": data["phone_number"],
        "type": "template",
        "template": {
            "name": data["hsm_name"],
            "language": {"code": data["code"]},
        },
    }

    if components:
        json["template"]["components"] = mounteds_components

    with requests.post(send_message_url, headers=headers, json=json) as response:
        message_data = response.json()
        WhatsAppPOST.objects.create(body=message_data)

    return response.status_code, message_data


def send_whatsapp_message(message, phone_number, replayed_message_id=None):
    json_data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "text",
        "text": {"preview_url": False, "body": f"{message}"},
    }
    if replayed_message_id:
        try:
            context_instance = Message.objects.values("whatsapp_message_id").get(
                id=replayed_message_id
            )
            json_data["context"] = {
                "message_id": context_instance["whatsapp_message_id"],
            }
        except ObjectDoesNotExist:
            context_instance = False

    with requests.post(send_message_url, headers=headers, json=json_data) as response:
        message_data = response.json()
        WhatsAppPOST.objects.create(body=response)

    return response.status_code, message_data
