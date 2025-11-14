import base64
import json
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import now
from django.views import View
from django.views.generic import (
    TemplateView, CreateView, DetailView, UpdateView
)

from config.settings import EMAIL_HOST_USER
from restic.forms import BookingCreateForm, BookingUpdateForm
from restic.mixins import ScreenshotHandlerMixin
from restic.models import Feedback, Booking, Table
from users.services import send_telegram_message_with_photo


class RestHomeView(TemplateView):
    '''ГЛАВНАЯ СТРАНИЦА + ФОРМА ФИДБЕКА'''
    template_name = 'restic/index.html'

    def post(self, request):
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if email and message:
            Feedback.objects.create(email=email, message=message)

            try:
                email_msg = EmailMessage(
                    subject="Новый фидбек на сайте",
                    body=f"Вам новый фидбек от {name}! Сообщение: {message[:50]}...\n Подробности в админ панели!",
                    to=[EMAIL_HOST_USER],
                )
                email_msg.send()
                messages.success(request, 'Спасибо! Ваше сообщение отправлено.')
            except Exception as e:
                messages.error(request, f'Сообщение сохранено, но уведомление не отправлено: {e}')
        else:
            messages.error(request, 'Пожалуйста, заполните все поля.')

        return redirect('restic:index')


class RestAboutView(TemplateView):
    '''ИНФОРМАЦИОННАЯ СТРАНИЦА'''
    template_name = 'restic/about.html'


class RestBookingView(ScreenshotHandlerMixin, CreateView):
    model = Booking
    form_class = BookingCreateForm
    template_name = 'restic/booking.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tables = Table.objects.filter(is_active=True)
        tables_data = [
            {"number": t.number, "capacity": t.capacity, "x": t.x, "y": t.y, "price": float(t.price)}
            for t in tables
        ]
        context['tables_json'] = json.dumps(tables_data)

        # Все бронирования для списка (только актуальные)
        context['bookings'] = Booking.objects.filter(is_cancelled=False).order_by('booking_date', 'booking_time')

        # Все бронирования для JS
        active_bookings = Booking.objects.filter(is_cancelled=False)
        bookings_data = []
        for booking in active_bookings:
            start = datetime.combine(booking.booking_date, booking.booking_time)
            end = start + booking.booking_period
            bookings_data.append({
                'id': booking.id,
                'table_numbers': list(booking.tables.values_list('number', flat=True)),
                'start_datetime': start.isoformat(),
                'end_datetime': end.isoformat(),
            })
        context['bookings_json'] = json.dumps(bookings_data)

        return context

    def get_success_url(self):
        return reverse_lazy('restic:booking')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.handle_screenshot(self.object)

        user = self.request.user
        if user.is_authenticated and user.telegram_chat_id:
            tables_list = ', '.join([f"#{t.number}" for t in self.object.tables.all()])
            message = (
                f"✅ Бронь № {self.object.id} подтверждена!\n"
                f"📅 Дата: {self.object.booking_date}\n"
                f"🕕 Время: {self.object.booking_time}\n"
                f"🪑 Столы: {tables_list}\n"
                f"💰 Сумма: {self.object.total_amount} ₽"
            )

            photo_path = None
            if self.object.screenshot:
                photo_path = self.object.screenshot.name  # путь относительно MEDIA_ROOT

            try:
                send_telegram_message_with_photo(
                    chat_id=user.telegram_chat_id,
                    message=message,
                    photo_path=photo_path
                )
            except Exception as e:
                print(f"Ошибка отправки Telegram: {e}")

        return response


class BookingDetailView(DetailView):
    model = Booking
    template_name = 'restic/booking_detail.html'
    context_object_name = 'booking'


class BookingUpdateView(UserPassesTestMixin, UpdateView):
    '''Редактирование бронирования с новой формой'''
    model = Booking
    form_class = BookingUpdateForm
    template_name = 'restic/booking_edit.html'
    success_url = reverse_lazy('restic:booking')

    def test_func(self):
        booking = self.get_object()
        return self.request.user.is_staff or (self.request.user.is_authenticated and booking.user == self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tables = Table.objects.filter(is_active=True)
        tables_data = [
            {"number": t.number, "capacity": t.capacity, "x": t.x, "y": t.y, "price": float(t.price)}
            for t in tables
        ]
        context['tables_json'] = json.dumps(tables_data)

        bookings_data = []
        for booking in Booking.objects.exclude(pk=self.object.pk).filter(is_cancelled=False):
            start = datetime.combine(booking.booking_date, booking.booking_time)
            end = start + booking.booking_period
            bookings_data.append({
                'id': booking.id,
                'table_numbers': list(booking.tables.values_list('number', flat=True)),
                'start_datetime': start.isoformat(),
                'end_datetime': end.isoformat(),
            })
        context['bookings_json'] = json.dumps(bookings_data)

        context['selected_tables_initial'] = list(self.object.tables.values_list('number', flat=True))
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        user = self.request.user
        if user.is_authenticated and user.telegram_chat_id:
            tables_list = ', '.join([f"#{t.number}" for t in self.object.tables.all()])
            message = (
                f"✅ Бронь № {self.object.id} отредактирована!\n"
                f"📅 Дата: {self.object.booking_date}\n"
                f"🕕 Время: {self.object.booking_time}\n"
                f"🪑 Столы: {tables_list}\n"
                f"💰 Сумма: {self.object.total_amount} ₽"
            )

            photo_path = self.object.screenshot.name if self.object.screenshot else None

            try:
                send_telegram_message_with_photo(
                    chat_id=user.telegram_chat_id,
                    message=message,
                    photo_path=photo_path
                )
            except Exception as e:
                print(f"Ошибка отправки Telegram: {e}")

        return response


class BookingCancelView(UserPassesTestMixin, View):
    """Запрос на отмену бронирования от пользователя"""
    def test_func(self):
        booking = get_object_or_404(Booking, pk=self.kwargs['pk'])
        return self.request.user.is_staff or (self.request.user.is_authenticated and booking.user == self.request.user)

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        booking.is_cancelled = True
        booking.cancelled_at = timezone.now()
        booking.save()
        messages.success(request, "Бронирование отменено.")
        return redirect('restic:booking_detail', pk=booking.pk)




class TestAboutView(TemplateView):
    '''ТЕСТОВАЯ СТРАНИЦА'''
    template_name = 'restic/test.html'