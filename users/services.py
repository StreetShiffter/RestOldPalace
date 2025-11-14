from django.conf import settings
import requests
from django.core.files.storage import default_storage


def send_telegram_message(chat_id, message):
    """Функция отправки сообщения боту в телеграм"""
    params = {
        "text": message,
        "chat_id": chat_id,
    }
    url = f"{settings.TELEGRAM_URL}{settings.TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, params=params)
    return response


def send_telegram_message_with_photo(chat_id, message, photo_path=None):
    """Функция отправки сообщения боту в телеграм бронирования со скриншотом"""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/"

    if photo_path and default_storage.exists(photo_path):
        # Отправка фото с подписью
        with default_storage.open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            data = {
                'chat_id': chat_id,
                'caption': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url + 'sendPhoto', data=data, files=files)
    else:
        # Обычное текстовое сообщение
        data = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
        response = requests.post(url + 'sendMessage', data=data)

    return response
