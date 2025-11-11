import json

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView, CreateView, ListView, DetailView

from config.settings import EMAIL_HOST_USER
from restic.forms import BookingCreateForm
from restic.models import Feedback, Booking, Table
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


class RestBookingView(CreateView):
    model = Booking
    form_class = BookingCreateForm
    template_name = 'restic/booking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаём данные столов в шаблон для JS
        tables = Table.objects.filter(is_active=True)
        tables_data = [
            {
                "number": t.number,
                "capacity": t.capacity,
                "x": t.x,
                "y": t.y
            }
            for t in tables
        ]
        context['tables_json'] = json.dumps(tables_data)

        date = self.request.GET.get('date')
        time = self.request.GET.get('time')
        occupied_tables = []
        if date and time:
            occupied = Booking.objects.filter(
                booking_date=date,
                booking_time=time
            ).values_list('tables__number', flat=True)
            occupied_tables = list(occupied)
        context['occupied_tables'] = json.dumps(occupied_tables)
        return context


    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('restic:booking_detail', kwargs={'pk': self.object.pk})


class BookingDetailView(DetailView):
    model = Booking
    template_name = 'restic/booking_detail.html'
    context_object_name = 'booking'

class TestAboutView(TemplateView):
    '''ТЕСТОВАЯ СТРАНИЦА'''
    template_name = 'restic/test.html'

