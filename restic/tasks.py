from datetime import timedelta, datetime

from celery import shared_task
from django.utils import timezone
from .models import Booking
from users.services import send_telegram_message


@shared_task
def cancel_unpaid_booking(booking_id):
    """Механизм отмены заказа, если не оплатил в течении 15 минут (RestBookingView)"""
    try:
        booking = Booking.objects.get(id=booking_id, is_cancelled=False)
        payment = getattr(booking, "payment", None)

        # Если оплата так и не подтверждена
        if not payment or payment.status not in ["paid", "check"]:
            booking.is_cancelled = True
            booking.cancelled_at = timezone.now()
            booking.save(update_fields=["is_cancelled", "cancelled_at"])

            # Уведомление в Telegram
            if booking.user and booking.user.telegram_chat_id:
                message = f"⏰ Время на оплату брони №{booking.id} истекло. Бронирование отменено."
                send_telegram_message(booking.user.telegram_chat_id, message)

    except Booking.DoesNotExist:
        pass  # уже отменена или удалена


@shared_task
def cancel_expired_bookings():
    """Отменяет брони, которые начались более 10 минут от начала брони - автоочистка брони для новых клиентов"""
# Вводные времени сейчас и с интервалом -10 минут
    now = timezone.now()
    threshold = now - timedelta(minutes=10)

# Фильтр брони
    expired = Booking.objects.filter(
        is_cancelled=False,
        is_sold=False,
        #SELECT * FROM booking WHERE booking_date <= '2025-11-20';
        booking_date__lte=now.date(),
    )
# Счетчик отмены и уведомлений
    count_cancelled = 0
    count_notified = 0

    for booking in expired:
        # Что бы посмотреть стартовое время .make_aware склеивает отдельные дату и время модели
        # и совмещает с таймзоной из settings
        start_time = timezone.make_aware(
            datetime.combine(booking.booking_date, booking.booking_.make_aware),
            timezone.get_default_timezone(),
        )
        if start_time <= threshold:
            # Отменяем бронь если не отменена и обновляем поля в БД
            if not booking.is_cancelled:
                booking.is_cancelled = True
                booking.cancelled_at = now
                booking.save(update_fields=["is_cancelled", "cancelled_at"])
                count_cancelled += 1

            # Отправляем уведомление ТОЛЬКО ОДИН РАЗ
            if (
                booking.user
                and booking.user.telegram_chat_id
                and not booking.telegram_end_notification_sent # если в модели False
            ):
                message = f"Бронь №{booking.id} завершена. Спасибо, что посетили нас!"
                send_telegram_message(booking.user.telegram_chat_id, message)
                booking.telegram_end_notification_sent = True
                booking.save(update_fields=["telegram_end_notification_sent"])
                count_notified += 1

    print(f"Отменено броней: {count_cancelled}, отправлено уведомлений: {count_notified}")
