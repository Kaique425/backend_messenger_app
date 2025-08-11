from io import BytesIO
from typing import NamedTuple, Optional, Set

import pandas as pd
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile
from django.db.models import F
from pandas import DataFrame
from phonenumbers import PhoneNumber, PhoneNumberFormat, parse
from PIL import Image

from chat.models import Attendance, Contact, Message, WabaChannel


class FormattedPhone(NamedTuple):
    length: int
    number: PhoneNumber


class ValidatedCsv(NamedTuple):
    df: DataFrame | None
    error_message: str | None


def get_message_by_wamid(wadi: str) -> Message | None:
    message: Message | None = Message.objects.filter(
        whatsapp_message_id=wadi,
    ).first()

    return message


def get_channel_by_number(channel_number: str) -> WabaChannel | None:

    attendance_channel: Optional[WabaChannel] = cache.get(channel_number)

    if attendance_channel is None:
        try:
            attendance_channel = WabaChannel.objects.get(
                channel_phone=channel_number,
            )
            cache.set(channel_number, attendance_channel, timeout=3600)

        except Exception as e:
            print(f"⛔- ERROR: {e}")

        try:
            attendance_channel = WabaChannel.objects.filter().first()
            cache.set(channel_number, attendance_channel, timeout=3600)

        except Exception as e:
            print(f"⛔- ERROR: {e}")

    return attendance_channel


def link_message_to_attendance(phone_number, message_instance, channel_number):
    was_changed = False
    try:
        last_open_attendance = Attendance.objects.get(
            customer_phone_number=phone_number, is_closed=False
        )

        channel_instance = get_channel_by_number(channel_number)

        message_instance.attendance = last_open_attendance

        if last_open_attendance.sector is None:
            last_open_attendance.sector = channel_instance.default_sector
            was_changed = True
        if not last_open_attendance.attendance_channel:
            last_open_attendance.attendance_channel = channel_number
            was_changed = True
        if (
            message_instance.send_by_operator
            and last_open_attendance.last_message_was_sent_by_operator is not True
        ):
            last_open_attendance.last_message_was_sent_by_operator = True
            last_open_attendance.unread_messages_quantity = 0
            was_changed = True

        elif message_instance.send_by_operator is False:
            Attendance.objects.filter(pk=last_open_attendance.pk).update(
                unread_messages_quantity=F("unread_messages_quantity") + 1,
                last_message_was_sent_by_operator=False,
            )
            last_open_attendance.refresh_from_db()
            was_changed = True

        if was_changed:
            last_open_attendance.save()
        message_instance.save()

    except Attendance.DoesNotExist:
        contact = Contact.objects.get(
            phone=phone_number,
        )

        channel_instance = get_channel_by_number(channel_number)
        new_attendance = Attendance.objects.create(
            customer_phone_number=contact.phone,
            customer_name=contact.name if contact else None,
            attendance_channel=channel_number,
            sector=channel_instance.default_sector,
        )
        if message_instance.type == "hsm":
            new_attendance.last_message_was_sent_by_operator = True

        message_instance.attendance = new_attendance
        message_instance.save()
        new_attendance.save()


def binary_to_webp(binary) -> BytesIO:
    image = Image.open(BytesIO(binary))
    output: BytesIO = BytesIO()
    image.save(output, "WEBP")
    output.seek(0)

    return output


def format_phone_number(initial_phone_number: str) -> FormattedPhone:
    parsed_phone: PhoneNumber = parse(initial_phone_number, None)
    full_number = phonenumbers.format_number(
        parsed_phone,
        PhoneNumberFormat.E164,
    )
    phone_length = len(full_number)

    return FormattedPhone(phone_length, parsed_phone)


def get_valid_phone_number(initial_phone_number: str) -> str | None:
    try:
        if not initial_phone_number.startswith("+"):
            initial_phone_number = "+" + initial_phone_number.strip("+")

        parsed_phone: FormattedPhone = format_phone_number(
            initial_phone_number,
        )

        if parsed_phone.length < 10:
            return None

        if not phonenumbers.is_valid_number(parsed_phone.number):
            return None

        return phonenumbers.format_number(
            parsed_phone.number,
            PhoneNumberFormat.E164,
        )

    except phonenumbers.phonenumberutil.NumberParseException:
        return None


def validate_contacts_csv(contacts_file: UploadedFile) -> ValidatedCsv:
    required_columns: Set[str] = getattr(
        settings,
        "CONTACTS_IMPORT_REQUIRED_COLUMNS",
    )

    if not contacts_file:
        return ValidatedCsv(None, "Any file was found!")

    filename = str(contacts_file)

    if not filename.endswith(".csv"):
        return ValidatedCsv(
            None,
            "Only csv files are valid to import contacts, convert the file to csv and try again!",
        )

    df: DataFrame = pd.read_csv(contacts_file, dtype="string")

    if not required_columns.issubset(df.columns):
        missing_columns: Set[str] = required_columns - set(df.columns)
        return ValidatedCsv(
            None,
            f"There are missings columns, please add them to the csv file: {missing_columns}",
        )

    return ValidatedCsv(df, None)
