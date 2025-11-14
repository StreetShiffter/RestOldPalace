import base64

from django.core.files.base import ContentFile
from django.utils.timezone import now


class ScreenshotHandlerMixin:
    def handle_screenshot(self, booking):
        screenshot_data = self.request.POST.get('screenshot_data')
        if screenshot_data and screenshot_data.startswith('image'):
            try:
                if ';base64,' in screenshot_data:
                    _, encoded = screenshot_data.split(';base64,', 1)
                else:
                    encoded = screenshot_data.split(',')[1]
                image_data = base64.b64decode(encoded)

                # 1. Удаляем старый скриншот, если он есть
                if booking.screenshot:
                    booking.screenshot.delete(save=False)  # ← УДАЛЯЕМ СТАРЫЙ ФАЙЛ

                # 2. Генерируем новое имя
                filename = f"booking_{booking.id}_{now().strftime('%Y%m%d_%H%M%S')}.png"

                # 3. Сохраняем новый файл (без сохранения объекта)
                booking.screenshot.save(filename, ContentFile(image_data), save=False)

                # 4. Явно сохраняем поле screenshot в БД
                booking.save(update_fields=['screenshot'])

            except Exception as e:
                print(f"Ошибка сохранения скриншота: {e}")