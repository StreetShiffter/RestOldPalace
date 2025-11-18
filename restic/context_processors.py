from datetime import timedelta, datetime

from django.db.models import ExpressionWrapper
from django.forms import DateTimeField
from django.utils import timezone
from django.db.models import F, Q

from .models import Feedback, Payment, Booking


def unread_feedback(request):
    '''Отдельная функция оповещения для админа в шапке(включен в TEMPLATES)'''
    if request.user.is_staff:
        return {
            'unread_feedback_count': Feedback.objects.filter(is_read=False).count()
        }
    return {}

def new_payment(request):
    '''Отдельная функция оповещения для админа в шапке(включен в TEMPLATES)'''
    if request.user.is_staff:
        return {
            'new_pay_count': Payment.objects.filter(is_read=False).count()
        }
    return {}

def user_notifications(request):
    '''Отдельная функция оповещения пользователю в шапке(включен в TEMPLATES)
    -формирование брони
    -изменение брони
    -оплата брони
    -отмена брони'''
    unread = False
    if request.user.is_authenticated:
        unread = request.user.bookings.filter(payment__is_read=False).exists()
    return {'unread_payments_exists': unread}

