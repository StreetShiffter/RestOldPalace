import secrets
from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django import forms
from django.db.models import Sum
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import CreateView, UpdateView, ListView
from config.settings import EMAIL_HOST_USER
from restic.models import Booking, Payment
from .forms import CustomUserCreationForm, UserProfileForm, CustomAuthenticationForm
from django.views import View
from django.urls import reverse_lazy
from .models import User

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .services import send_telegram_message


class UserRegisterView(CreateView):
    """Контроллер регистрации пользователя"""

    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = form.save(commit=False)  # Сохраняем пользователя без логирования
        user.is_active = False  # Деактивируем
        token = secrets.token_hex(16)  # Генерация токена
        user.token = token
        user.save()

        # === Отправка Telegram =============
        if user.telegram_chat_id:
            try:
                message = "🎉 Добро пожаловать в ресторан Grill House! Я ваш помощник по бронированию и оплате столиков."
                send_telegram_message(chat_id=user.telegram_chat_id, message=message)
            except Exception as e:
                print(f"Ошибка отправки Telegram: {e}")
        # ====================================

        host = self.request.get_host()
        url = f"http://{host}/users/email-confirm/{token}/"

        # Рендерим HTML-письмо
        html_message = render_to_string('users/email_confirmation.html', {
            'protocol': 'http',
            'domain': host,
            'url': url,
        })

        # Текстовая версия (на случай, если клиент не поддерживает HTML)
        plain_message = strip_tags(html_message)

        send_mail(
            subject="Подтверждение почты",
            message=plain_message,
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message,  # ← ключевая строка!
        )

        messages.info(self.request, "Проверьте почту для подтверждения email.")
        return redirect(self.success_url)


def email_verification(request, token):
    user = get_object_or_404(User, token=token)

    if user.is_active:
        # Уже активен — просто перенаправляем
        return redirect("users:login")

    # Активируем
    user.is_active = True
    user.token = None  # Обнуляем токен, что бы можно было восстановить пароль по новому токену ТРАБЛ
    user.save()

    # Можно добавить сообщение на странице логина
    messages.success(request, "Email подтверждён! Теперь можно войти.")

    return redirect("users:login")


class CustomLoginView(LoginView):
    '''Кастомное создание пользователя: проверяем скрытно, есть ли почта в БД.
    Если есть, но не правильный пароль, то покажем кнопку "Забыли пароль?"
    Если нет - обобщающая плашка неправильно что-то одно'''
    template_name = "users/login.html"
    success_url = reverse_lazy("users:profile")
    form_class = CustomAuthenticationForm

    def form_invalid(self, form):
        # Передаём в контекст, существует ли email — для показа кнопки "Забыли пароль?"
        username = form.data.get('username')
        email_exists = User.objects.filter(email=username).exists() if username else False

        context = self.get_context_data(form=form)
        context['email_exists'] = email_exists
        return self.render_to_response(context)

    def form_valid(self, form):
        user = form.get_user()
        if user.token:
            user.token = None
            user.save()
        return super().form_valid(form)


class UserProfileView(View):
    '''Вьюшка просмотра профиля пользователя'''

    def get(self, request):
        user = request.user

        # Аннотируем сумму оплаченных бронирований
        user.paid_total = Booking.objects.filter(
            user=user,
            is_cancelled=False,
            payment__status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        bookings = Booking.objects.filter(user=user, is_cancelled=False)
        total_amount = sum(b.total_amount for b in bookings)

        return render(request, "users/profile.html", {
            'bookings': bookings,
            'total_amount': total_amount,        # все активные (неоплаченные в т.ч.)
            'paid_total': user.paid_total,       # только оплаченные
        })


class UserProfileEditView(LoginRequiredMixin, UpdateView):
    """Вьюшка редактирования кабинета пользователя(LoginRequiredMixi защищает от неавторизованности)"""

    model = User
    form_class = UserProfileForm
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user  # редактируем только текущего пользователя

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bookings'] = self.request.user.bookings.all()  # или как у вас называется related_name
        return context


##########################################################################################
# Администрирование
@login_required
def delete_user(request, pk):
    '''Механизм удаления самого себя'''
    if request.user.pk != pk:
        messages.error(request, "Вы можете удалить только свой аккаунт.")
        return redirect("restic:index")

    # Сохраняем имя для сообщения (до удаления!)
    username = request.user.get_full_name() or request.user.username
    request.user.delete()

    # Важно: разлогиниваемся ПОСЛЕ удаления, но до редиректа
    logout(request)

    messages.success(request, f"Ваш аккаунт {username} был успешно удалён.")
    return redirect("users:login")

