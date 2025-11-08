from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import TemplateView

from config.settings import EMAIL_HOST_USER
from restic.models import Feedback
from django.core.mail import EmailMessage


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
                    to=[EMAIL_HOST_USER],  # ЗАМЕНИ НА СВОЙ EMAIL
                )
                email_msg.send()
                messages.success(request, 'Спасибо! Ваше сообщение отправлено.')
            except Exception as e:
                print(f"Ошибка при отправке email: {e}")
                messages.error(request, f'Сообщение сохранено, но уведомление не отправлено: {e}')
        else:
            messages.error(request, 'Пожалуйста, заполните все поля.')

        return redirect('restic:index')


class RestAboutView(TemplateView):
    '''ИНФОРМАЦИОННАЯ СТРАНИЦА'''
    template_name = 'restic/about.html'
