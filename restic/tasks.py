from datetime import timedelta, datetime

from celery import shared_task
from django.utils import timezone
from .models import Booking
from users.services import send_telegram_message

@shared_task
def cancel_unpaid_booking(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, is_cancelled=False)
        payment = getattr(booking, 'payment', None)

        # Если оплата так и не подтверждена
        if not payment or payment.status not in ['paid', 'check']:
            booking.is_cancelled = True
            booking.cancelled_at = timezone.now()
            booking.save(update_fields=['is_cancelled', 'cancelled_at'])

            # Уведомление в Telegram
            if booking.user and booking.user.telegram_chat_id:
                message = f"⏰ Время на оплату брони №{booking.id} истекло. Бронирование отменено."
                send_telegram_message(booking.user.telegram_chat_id, message)

    except Booking.DoesNotExist:
        pass  # уже отменена или удалена


@shared_task
def cancel_expired_bookings():
    """Отменяет брони, которые начались более 10 минут назад и не подтверждены."""
    now = timezone.now()
    threshold = now - timedelta(minutes=10)

    # Брони, которые начались >10 мин назад, не отменены и не проданы
    expired = Booking.objects.filter(
        is_cancelled=False,
        is_sold=False,
        booking_date__lte=now.date(),
    )

    count = 0
    for booking in expired:
        start_time = timezone.make_aware(
            datetime.combine(booking.booking_date, booking.booking_time),
            timezone.get_default_timezone()
        )
        if start_time <= threshold:
            booking.is_cancelled = True
            booking.cancelled_at = now
            booking.save(update_fields=['is_cancelled', 'cancelled_at'])
            count += 1

    print(f"Отменено {count} просроченных броней.")