# restic/forms.py
import base64

from django import forms
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import timedelta, time, datetime

from django.utils.timezone import now

from .models import Booking, Table

def get_opening_hours_py(booking_date):
    """Возвращает (open_time, close_time) для заданной даты (date)"""
    # weekday(): Mon=0, ..., Sun=6
    weekday = booking_date.weekday()
    if weekday == 6:  # Воскресенье
        return time(12, 0), time(23, 59)
    elif weekday in (4, 5):  # Пятница=4, Суббота=5
        return time(11, 0), time(1, 0)  # 01:00 следующего дня — обрабатывается в clean()
    else:  # Пн–Чт
        return time(11, 0), time(23, 59)

class BookingCreateForm(forms.ModelForm):
    '''Форма для записи бронирования'''
    selected_tables = forms.CharField(widget=forms.HiddenInput())
    guest_first_name = forms.CharField(
        max_length=100,
        required=False,
        label="Ваше имя"
    )
    guest_last_name = forms.CharField(
        max_length=100,
        required=False,
        label="Ваша фамилия"
    )
    phone_for_unauthorized = forms.CharField(
        max_length=12,
        required=False,
        label="Ваш телефон (обязательно для гостей)",
        help_text="Мы свяжемся с вами для подтверждения брони"
    )
    duration_hours = forms.ChoiceField(
        choices=[(1, "1 час"), (2, "2 часа"), (3, "3 часа"), (4, "4 часа"), (6, "6 часов"), (8, "8 часов"), (12, "12 часов")],
        initial=2,
        label="Длительность"
    )

    screenshot_data = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Booking
        fields = ['booking_date', 'booking_time']
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date'}),
            'booking_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and self.user.is_authenticated:
            # Скрыть поля для авторизованных
            del self.fields['guest_first_name']
            del self.fields['guest_last_name']
            del self.fields['phone_for_unauthorized']
        else:
            # Для гостей — сделать телефон обязательным
            self.fields['phone_for_unauthorized'].required = True

    def clean_selected_tables(self):
        raw = self.cleaned_data['selected_tables']
        try:
            nums = [int(x) for x in raw.split(',') if x.strip()]
            tables = Table.objects.filter(number__in=nums, is_active=True)
            if len(tables) != len(nums):
                raise forms.ValidationError("Некоторые столы недоступны.")
            if not nums:
                raise forms.ValidationError("Выберите хотя бы один стол.")
            return nums
        except ValueError:
            raise forms.ValidationError("Неверный формат.")

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('booking_date')
        booking_time = cleaned_data.get('booking_time')
        duration_hours = cleaned_data.get('duration_hours')

        if not all([booking_date, booking_time, duration_hours]):
            return cleaned_data

        try:
            # Создаём naive datetime (без часового пояса)
            booking_start = datetime.combine(booking_date, booking_time)
        except Exception:
            raise forms.ValidationError("Некорректная дата или время.")

        # Получаем текущее время как datetime-объект
        now = timezone.now()

        # Если USE_TZ = True, то now — timezone-aware, а booking_start — naive
        # Приведём booking_start к тому же часовому поясу, что и now
        if timezone.is_aware(now):
            # Делаем booking_start aware в локальном часовом поясе
            booking_start = timezone.make_aware(
                booking_start,
                timezone.get_current_timezone()
            )

        if booking_start < now:
            raise forms.ValidationError("Нельзя бронировать на прошедшее время.")

        duration = timedelta(hours=int(duration_hours))
        booking_end = booking_start + duration

        open_time, close_time = get_opening_hours_py(booking_date)

        # Проверка времени открытия
        if booking_time < open_time:
            open_str = "01:00" if close_time == time(1, 0) and open_time == time(11, 0) and booking_date.weekday() in (4, 5) else open_time.strftime("%H:%M")
            raise forms.ValidationError(f"Ресторан открывается в {open_time.strftime('%H:%M')}.")

        # Проверка окончания
        if booking_date.weekday() in (4, 5):  # Пт/Сб — можно до 01:00 следующего дня
            # Разрешаем окончание на следующий день, но не позже 01:00
            if booking_end.date() == booking_date:
                # Завершается в тот же день — должно быть <= 23:59
                if booking_end.time() > time(23, 59):
                    raise forms.ValidationError("В этот день бронирование может завершиться не позже 01:00 следующего дня.")
            elif booking_end.date() == booking_date + timedelta(days=1):
                # Завершается на следующий день — должно быть <= 01:00
                if booking_end.time() > time(1, 0):
                    raise forms.ValidationError("Бронирование в выходные не может завершиться позже 01:00.")
            else:
                raise forms.ValidationError("Бронирование не может длиться более суток.")
        else:
            # Пн–Чт, Вс — только в тот же день
            if booking_end.date() != booking_date:
                raise forms.ValidationError("В этот день бронирование должно завершиться в пределах суток.")
            if booking_end.time() > close_time:
                raise forms.ValidationError(f"Бронирование не может завершиться позже {close_time.strftime('%H:%M')}.")

        cleaned_data['booking_period'] = duration
        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.booking_period = self.cleaned_data['booking_period']

        if self.user and self.user.is_authenticated:
            booking.user = self.user
        else:
            # ← ДОБАВЬТЕ ЭТИ ДВЕ СТРОКИ
            booking.guest_first_name = self.cleaned_data.get('guest_first_name')
            booking.guest_last_name = self.cleaned_data.get('guest_last_name')
            booking.phone_for_unauthorized = self.cleaned_data['phone_for_unauthorized']

        if commit:
            booking.save()
            table_numbers = self.cleaned_data['selected_tables']
            tables = Table.objects.filter(number__in=table_numbers)
            booking.tables.set(tables)

            total = sum(table.price for table in booking.tables.all())
            booking.total_amount = total
            booking.save(update_fields=['total_amount'])

            screenshot_data = self.cleaned_data.get('screenshot_data')
            if screenshot_data:
                try:
                    if screenshot_data.startswith('data:image'):
                        header, encoded = screenshot_data.split(',', 1)
                    else:
                        encoded = screenshot_data
                    binary_data = base64.b64decode(encoded)
                    file = ContentFile(binary_data, name=f'booking_{booking.pk}.png')
                    booking.screenshot.save(file.name, file, save=True)
                except Exception as e:
                    print(f"Ошибка сохранения скриншота: {e}")

        return booking

class BookingUpdateForm(BookingCreateForm):
    """Форма для редактирования брони — удаляет старый скриншот перед сохранением"""

    def save(self, commit=True):
        booking = super().save(commit=False)  # ← commit=False!
        booking.booking_period = self.cleaned_data['booking_period']

        if self.user and self.user.is_authenticated:
            booking.user = self.user
        else:
            booking.phone_for_unauthorized = self.cleaned_data['phone_for_unauthorized']

        # Сначала обновим связанные данные (таблицы, сумма), но НЕ сохраняем в БД
        table_numbers = self.cleaned_data['selected_tables']
        tables = Table.objects.filter(number__in=table_numbers)

        total = sum(table.price for table in tables)
        booking.total_amount = total

        if commit:
            booking.save()
            booking.tables.set(tables)
            booking.total_amount = total
            booking.save(update_fields=['total_amount'])

            # === ОТЛАДКА ===
            screenshot_data = self.cleaned_data.get('screenshot_data')
            print(">>> screenshot_data:", screenshot_data[:100] if screenshot_data else "None")
            print(">>> booking.pk:", booking.pk)

            if booking.screenshot:
                try:
                    booking.screenshot.delete(save=False)
                except Exception as e:
                    print(f"Ошибка удаления: {e}")
            booking.screenshot = None

            if screenshot_data:
                try:
                    # Проверяем формат
                    if screenshot_data.startswith('data:image'):
                        _, encoded = screenshot_data.split(',', 1)
                    else:
                        encoded = screenshot_data
                    print(">>> Длина encoded:", len(encoded))

                    binary_data = base64.b64decode(encoded)
                    print(">>> Размер binary_data:", len(binary_data))

                    filename = f"booking_{booking.pk}_{now().strftime('%Y%m%d_%H%M%S')}.png"
                    file = ContentFile(binary_data, name=filename)
                    booking.screenshot.save(filename, file, save=True)  # ← save=True
                    print(">>> Новый скриншот сохранён:", filename)
                except Exception as e:
                    print(f"❗ Ошибка сохранения нового скриншота: {e}")
            else:
                print(">>> Нет данных для скриншота!")

        return booking

