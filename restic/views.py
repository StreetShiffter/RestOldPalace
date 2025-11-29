from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from restic.tasks import cancel_unpaid_booking
import os

from django.db.models import Sum
import json
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import EmailMessage
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, ListView

from config.settings import EMAIL_HOST_USER
from restic.forms import BookingCreateForm, BookingUpdateForm
from restic.mixins import ScreenshotHandlerMixin
from restic.models import Feedback, Booking, Table, Payment, CommandWorker
from restic.video_carusel import get_vk_video_urls
from users.services import send_telegram_message_with_photo

# Генерация ссылки СБП с суммой
from urllib.parse import urlencode


class RestHomeView(TemplateView):
    """ГЛАВНАЯ СТРАНИЦА + ФОРМА ФИДБЕКА"""

    template_name = "restic/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["vk_video_urls"] = get_vk_video_urls()
        return context

    def post(self, request):
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        if email and message:
            Feedback.objects.create(email=email, message=message)

            try:
                email_msg = EmailMessage(
                    subject="Новый фидбек на сайте",
                    body=f"Вам новый фидбек от {name}! Сообщение: {message[:50]}...\n Подробности в админ панели!",
                    to=[EMAIL_HOST_USER],
                )
                email_msg.send()
                messages.success(request, "Спасибо! Ваше сообщение отправлено.")
            except Exception as e:
                messages.error(
                    request, f"Сообщение сохранено, но уведомление не отправлено: {e}"
                )
        else:
            messages.error(request, "Пожалуйста, заполните все поля.")

        return redirect("restic:index")


class RestAboutView(ListView):
    """ИНФОРМАЦИОННАЯ СТРАНИЦА + Комманда"""
    model = CommandWorker
    template_name = "restic/about.html"
    context_object_name = "staff"


class RestBookingView(ScreenshotHandlerMixin, CreateView):
    """Страница бронирования и отображения динамических броней"""

    model = Booking
    form_class = BookingCreateForm
    template_name = "restic/booking.html"

    def get_success_url(self):
        return reverse_lazy("restic:booking")

    def get_form_kwargs(self):
        """Если пользователь есть, то достаем его и отдаем в форму, что бы было понятно кто заполняет
        для случая, когда форма должна быть предзаполнена данными текущего пользователя
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаем наши столики в виде json для работы JS в шаблоне
        tables = Table.objects.all()
        tables_data = [
            {
                "number": t.number,
                "capacity": t.capacity,
                "x": t.x,
                "y": t.y,
                "price": float(t.price),
                "is_active": t.is_active,
            }
            for t in tables
        ]
        context["tables_json"] = json.dumps(tables_data)

        # Все бронирования для списка (только актуальные)
        context["bookings"] = Booking.objects.filter(is_cancelled=False).order_by(
            "booking_date", "booking_time"
        )

        # Все бронирования для JS (получаем только активные)
        active_bookings = Booking.objects.filter(is_cancelled=False)
        bookings_data = []
        for booking in active_bookings:
            start = datetime.combine(booking.booking_date, booking.booking_time)
            end = start + booking.booking_period
            bookings_data.append(
                {
                    "id": booking.id,
                    # .values_list('number', flat=True)
                    # .values_list() — выбирает только указанные поля из базы (вместо целых объектов).
                    # 'number' — номера столов.
                    # flat=True — если запрашиваем одно поле, верни список значений, а не кортежи.
                    # вместо [(5,), (7,)] получим [5, 7]
                    "table_numbers": list(
                        booking.tables.values_list("number", flat=True)
                    ),
                    # Готовые время и дата обворачиваем в .isoformat() в
                    # строку вида "2025-11-17T19:00:00", которую JS легко парсит.
                    "start_datetime": start.isoformat(),
                    "end_datetime": end.isoformat(),
                }
            )
        context["bookings_json"] = json.dumps(bookings_data)

        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        # Активируем миксин для создания скриншота карты столов для отправки в телеграм и отображения в профиле
        self.handle_screenshot(self.object)

        # Обновляем total_order_amount пользователя
        if self.request.user.is_authenticated:
            total = (
                Booking.objects.filter(
                    user=self.request.user, is_cancelled=False
                ).aggregate(total=Sum("total_amount"))["total"]
                or 0
            )
            self.request.user.total_order_amount = total
            self.request.user.save(update_fields=["total_order_amount"])

        payment, created = Payment.objects.get_or_create(
            booking=self.object, defaults={"amount": self.object.total_amount}
        )

        base_sbp_url = os.getenv("PAYMENT", "https://www.tinkoff.ru/rm/...")
        params = urlencode(
            {"sum": str(self.object.total_amount), "desc": f"Бронь №{self.object.id}"}
        )
        payment.qr_url = f"{base_sbp_url}?{params}"
        payment.save(update_fields=["qr_url"])

        user = self.request.user
        if user.is_authenticated and user.telegram_chat_id:
            tables_list = ", ".join([f"#{t.number}" for t in self.object.tables.all()])
            message = (
                f"✅ Бронь № {self.object.id} подтверждена!\n"
                f"📅 Дата: {self.object.booking_date}\n"
                f"🕕 Время: {self.object.booking_time}\n"
                f"🪑 Столы: {tables_list}\n"
                f"💰 Сумма: {self.object.total_amount} ₽\n"
                f"🔗 Ссылка на оплату: {base_sbp_url}"
            )

            photo_path = None
            if self.object.screenshot:
                photo_path = self.object.screenshot.name

            try:
                send_telegram_message_with_photo(
                    chat_id=user.telegram_chat_id,
                    message=message,
                    photo_path=photo_path,
                )
            except Exception as e:
                print(f"Ошибка отправки Telegram: {e}")

        # Запуск отмены через 15 минут (celery beat)
        cancel_unpaid_booking.apply_async(
            args=[self.object.id], countdown=15 * 60  # 15 минут
        )

        return response


class BookingDetailView(DetailView):
    '''Просмотр бронирования'''
    model = Booking
    template_name = "restic/booking_detail.html"
    context_object_name = "booking"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.object

        # Добавляем ссылку на оплату, если оплата не завершена
        try:
            payment = booking.payment
            if payment.status == Payment.Status.CREATED:
                from urllib.parse import urlencode

                base_sbp_url = (
                    "https://www.tinkoff.ru/rm/r_kaOSbVmlxH.ztwoywaUzK/e5Em943815"
                )
                params = urlencode(
                    {"sum": str(booking.total_amount), "desc": f"Бронь №{booking.id}"}
                )
                context["payment_url"] = f"{base_sbp_url}?{params}"
        except Payment.DoesNotExist:
            # Если оплата ещё не создана — тоже показываем ссылку
            from urllib.parse import urlencode

            base_sbp_url = (
                "https://www.tinkoff.ru/rm/r_kaOSbVmlxH.ztwoywaUzK/e5Em943815"
            )
            params = urlencode(
                {"sum": str(booking.total_amount), "desc": f"Бронь №{booking.id}"}
            )
            context["payment_url"] = f"{base_sbp_url}?{params}"

            # Запуск отмены через 15 минут (celery beat)
            cancel_unpaid_booking.apply_async(
                args=[self.object.id], countdown=15 * 60  # 15 минут
            )

        return context


class BookingUpdateView(UserPassesTestMixin, UpdateView):
    """Редактирование бронирования с новой формой"""

    model = Booking
    form_class = BookingUpdateForm
    template_name = "restic/booking_edit.html"
    success_url = reverse_lazy("restic:booking")

    def test_func(self):
        booking = self.get_object()
        return self.request.user.is_staff or (
            self.request.user.is_authenticated and booking.user == self.request.user
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tables = Table.objects.filter(is_active=True)
        tables_data = [
            {
                "number": t.number,
                "capacity": t.capacity,
                "x": t.x,
                "y": t.y,
                "price": float(t.price),
            }
            for t in tables
        ]
        context["tables_json"] = json.dumps(tables_data)

        bookings_data = []
        for booking in Booking.objects.exclude(pk=self.object.pk).filter(
            is_cancelled=False
        ):
            start = datetime.combine(booking.booking_date, booking.booking_time)
            end = start + booking.booking_period
            bookings_data.append(
                {
                    "id": booking.id,
                    "table_numbers": list(
                        booking.tables.values_list("number", flat=True)
                    ),
                    "start_datetime": start.isoformat(),
                    "end_datetime": end.isoformat(),
                }
            )
        context["bookings_json"] = json.dumps(bookings_data)

        context["selected_tables_initial"] = list(
            self.object.tables.values_list("number", flat=True)
        )
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        user = self.request.user
        if user.is_authenticated and user.telegram_chat_id:
            tables_list = ", ".join([f"#{t.number}" for t in self.object.tables.all()])
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
                    photo_path=photo_path,
                )
            except Exception as e:
                print(f"Ошибка отправки Telegram: {e}")

        return response


class BookingCancelView(UserPassesTestMixin, View):
    """Запрос на отмену бронирования от пользователя"""

    def test_func(self):
        booking = get_object_or_404(Booking, pk=self.kwargs["pk"])
        return self.request.user.is_staff or (
            self.request.user.is_authenticated and booking.user == self.request.user
        )

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        booking.is_cancelled = True
        booking.cancelled_at = timezone.now()
        booking.save()
        messages.success(request, "Бронирование отменено.")
        return redirect("restic:booking_detail", pk=booking.pk)


@login_required
def mark_all_payments_read(request):
    if request.method == "POST":
        Payment.objects.filter(booking__user=request.user, is_read=False).update(
            is_read=True
        )
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)


class TestAboutView(TemplateView):
    """ТЕСТОВАЯ СТРАНИЦА"""

    template_name = "restic/test.html"
