import requests

from .models import Message

AUTH_TOKEN = "EAAKhMTEACSEBAGMS1YQSkvhi7E7fdfPDYRGZClVlWSQlzlsWTfQ1EZCLjZCxPBHTcGl1J9oWZBAU3hElwulgAKdFiYBd4AvgfdJ350gPlzQ0QC0UcSyo8xfkyBZBGJFzCTsiHT7tFl9k8tFceDks66BP4ahf1l8E0CxCLEBXu18v1xqZBM8a5TaHrnJJEpY705ZAwoyrVjqxctt8rvlkmiJ"

send_message_url = "https://graph.facebook.com/v16.0/101917902878484/messages"

headers = {"Content-Type": "application/json", "Authorization": f"Bearer {AUTH_TOKEN}"}


def save_media_message():
    return True


def send_media_messages(file, caption):
    print(f"MEDIA URL {file} E CAPTION {caption}")
    json = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "5518996696477",
        "type": "image",
        "image": {"link": file, "caption": caption},
    }
    response = requests.post(url=send_message_url, headers=headers, json=json)

    print(f"STATUS DO CODE ===> {response.status_code}")
    data = response.json()
    return data, response.status_code


def get_media_url(media_id):
    try:
        url = f"https://graph.facebook.com/v16.0/{media_id}/"
        response = requests.get(url, headers=headers)
        data = response.json()

        status_code = response.status_code
        print(f"CURRENT DATA {data} WITH STATUS CODE {status_code}")
        media_url = data["url"]

        media_response = requests.get(media_url, headers=headers)

        return media_response
    except:
        print(f"Error status code {status_code}")


def send_whatsapp_hsm_message():
    json = {
        "messaging_product": "whatsapp",
        "to": "5518996696477",
        "type": "template",
        "template": {"name": "hello_world", "language": {"code": "en_US"}},
    }

    response = requests.post(send_message_url, headers=headers, json=json)

    return response.status_code


def send_whatsapp_message(message):
    json = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "5518996696477",
        "type": "text",
        "text": {"preview_url": False, "body": f"{message}"},
    }
    response = requests.post(send_message_url, headers=headers, json=json)

    if response.status_code == 200:
        message_infos = response.json()
        message = Message.objects.create(
            send_by_operator=True,
            whatsapp_message_id=message_infos["messages"][0]["id"],
            body=message,
            type="text",
        )
    return response.status_code
