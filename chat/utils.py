from io import BytesIO

from django.core.cache import cache
from PIL import Image

from chat.models import Attendance, Contact, Sector, WabaChannel


def get_channel_by_number(channel_number):

    attendance_channel = cache.get(channel_number)

    if attendance_channel is None:
        attendance_channel = WabaChannel.objects.get(
            channel_phone=channel_number,
        )
        cache.set(channel_number, attendance_channel, timeout=3600)

    return attendance_channel


def link_message_to_attendance(phone_number, message_instance, channel_number):

    try:
        last_open_attendance = Attendance.objects.get(
            customer_phone_number=phone_number, is_closed=False
        )

        channel_instance = get_channel_by_number(channel_number)

        message_instance.attendance = last_open_attendance

        if last_open_attendance.sector is None:
            last_open_attendance.sector = channel_instance.default_sector
            last_open_attendance.save()

        if last_open_attendance.attendance_channel == "":
            last_open_attendance.attendance_channel = channel_number
            last_open_attendance.save()

        if (
            message_instance.send_by_operator
            and last_open_attendance.last_message_was_sent_by_operator is not True
        ):
            last_open_attendance.last_message_was_sent_by_operator = True
            last_open_attendance.unread_messages_quantity = 0
            last_open_attendance.save()

        elif message_instance.send_by_operator is False:
            last_open_attendance.unread_messages_quantity += 1

            if last_open_attendance.last_message_was_sent_by_operator is True:
                last_open_attendance.last_message_was_sent_by_operator = False
            last_open_attendance.save()

        message_instance.save()

    except Attendance.DoesNotExist:
        print("ATENDIMENTO FOI CRIADO.")
        contact_info = Contact.objects.get(phone=phone_number)
        channel_instance = get_channel_by_number(channel_number)
        new_attendance = Attendance.objects.create(
            customer_phone_number=contact_info.phone,
            customer_name=contact_info.name,
            attendance_channel=channel_number,
            sector=channel_instance.default_sector,
        )
        message_instance.attendance = new_attendance


def binary_to_webp(binary):
    image = Image.open(BytesIO(binary))

    # Convert image to WebP format
    output = BytesIO()
    image.save(output, "WEBP")
    output.seek(0)

    return output
