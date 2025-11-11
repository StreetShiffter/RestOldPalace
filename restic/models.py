from django.db import models
from config import settings


class Table(models.Model):
    '''Модель карты столиков'''
    number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveSmallIntegerField(choices=[(2, '2'), (4, '4')])
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    x = models.FloatField()
    y = models.FloatField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Стол #{self.number} (на {self.capacity})"


class Booking(models.Model):
    '''Модель заказа столика'''
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             verbose_name="Клиент",
                             related_name="bookings")
    tables = models.ManyToManyField(Table, verbose_name="Столики")

    booking_date = models.DateField(verbose_name="Дата бронирования")
    booking_time = models.TimeField(verbose_name="Время бронирования")
    booking_period = models.TimeField(verbose_name="Длительность бронирования")

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма",
        editable=False  # будет считаться автоматически
    )
    screenshot = models.ImageField(
        upload_to='bookings/screenshots/',
        blank=True,
        null=True,
        verbose_name="Скриншот карты зала"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"

    def __str__(self):
        return f"Бронь {self.user.username} на {self.booking_date} в {self.booking_time}"

    def save(self, *args, **kwargs):
        # Автоматический расчёт суммы: 2 рубля за стол на 2, 4 рубля за стол на 4
        if not self.pk:  # только при создании
            total = 0
            for table in self.tables.all():
                total += table.price
            self.total_amount = total
        super().save(*args, **kwargs)

class Feedback(models.Model):
    email = models.EmailField(verbose_name="Email")
    message = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")

    class Meta:
        verbose_name = "Обратная связь"
        verbose_name_plural = "Обратная связь"

    def __str__(self):
        return f"Сообщение от {self.email}"
