from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Payment
from users.services import send_telegram_message


@receiver(post_save, sender=Payment)
def notify_user_on_payment_status_change(sender, instance, created, **kwargs):
    """Отслеживаем статуса заказа в админке"""
    if created:
        return  # при создании — не уведомляем

    booking = instance.booking
    user = booking.user
    if not user or not user.telegram_chat_id:
        return

    chat_id = user.telegram_chat_id
    if instance.status == "paid":
        message = f"🎉 Бронь №{booking.id} подтверждена! Оплата прошла успешно."
        send_telegram_message(chat_id, message)
    elif instance.status == Payment.Status.ABORT:
        message = f"❌ Оплата брони №{booking.id} отменена администратором."
        send_telegram_message(chat_id, message)
        # Опционально: пометить бронь как отменённую
        if not booking.is_cancelled:
            booking.is_cancelled = True
            booking.cancelled_at = timezone.now()
            booking.save(update_fields=["is_cancelled", "cancelled_at"])
