import base64

from django.core.files.base import ContentFile
from django.utils.timezone import now

# Принцип работы: На станице есть элемент <canvas>, который с помощью библиотеки html2canvas
# на стороне браузера делает скриншот. Изображение записывается в формате Data URL (base64) - работа в JS

# В шаблоне есть строка: <input type="hidden" name="screenshot_data" id="id_screenshot_data">
# которая в JS записывается:
# const imageData = canvas.toDataURL('image/png');
# document.getElementById('id_screenshot_data').value = imageData;


# Миксин в свою очередь обрабатывает url изображения и сохраняет в файл
class ScreenshotHandlerMixin:
    """Механизм захвата скриншота"""

    def handle_screenshot(self, booking):
        screenshot_data = self.request.POST.get("screenshot_data")
        if screenshot_data and screenshot_data.startswith("image"):
            try:
                if ";base64," in screenshot_data:
                    _, encoded = screenshot_data.split(";base64,", 1)
                else:
                    encoded = screenshot_data.split(",")[1]
                image_data = base64.b64decode(encoded)

                # Удаляем старый скриншот, если он есть
                if booking.screenshot:
                    booking.screenshot.delete(save=False)

                # Генерируем новое имя
                filename = f"booking_{booking.id}_{now().strftime('%Y%m%d_%H%M%S')}.png"

                # Сохраняем новый файл (без сохранения объекта)
                booking.screenshot.save(filename, ContentFile(image_data), save=False)

                # Явно сохраняем поле screenshot в БД
                booking.save(update_fields=["screenshot"])

            except Exception as e:
                print(f"Ошибка сохранения скриншота: {e}")
