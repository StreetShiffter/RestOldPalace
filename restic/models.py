from datetime import timedelta

from django.db import models
from config import settings


class Table(models.Model):
    """Модель карты столиков"""

    number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveSmallIntegerField(choices=[(2, "2"), (4, "4")])
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    x = models.FloatField()
    y = models.FloatField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Стол #{self.number} (на {self.capacity})"


class Booking(models.Model):
    """Модель закакза столиков"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Клиент",
        related_name="bookings",
    )
    guest_first_name = models.CharField("Имя", max_length=100, blank=True, null=True)
    guest_last_name = models.CharField("Фамилия", max_length=100, blank=True, null=True)
    phone_for_unauthorized = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        verbose_name="Телефон (если не авторизован)",
    )

    tables = models.ManyToManyField(Table, verbose_name="Столики")
    booking_date = models.DateField(verbose_name="Дата бронирования")
    booking_time = models.TimeField(verbose_name="Время начала")
    booking_period = models.DurationField(
        verbose_name="Длительность", default=timedelta(hours=2)
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Сумма",
        editable=False,
    )

    is_cancelled = models.BooleanField(default=False, verbose_name="Отменено")
    cancelled_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Время отмены"
    )
    is_sold = models.BooleanField(default=False)

    screenshot = models.ImageField(
        upload_to="bookings/screenshots/",
        blank=True,
        null=True,
        verbose_name="Скриншот карты зала",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        permissions = [('view_all_bookings', 'Может просматривать все брони'),]

    def __str__(self):
        if self.user:
            return f"👤 {self.user.email} — {self.booking_date} в {self.booking_time}"
        else:
            return f"📞 {self.phone_for_unauthorized} — {self.booking_date} в {self.booking_time}"


class Payment(models.Model):
    """Модель оплаты бронирования"""

    class Status(models.TextChoices):
        """Статус брони (вместо списка кортежей)"""

        ABORT = "abort", "Отменен"
        CREATED = "created", "Создан"
        CHECK = "check", "На проверке"
        PAID = "paid", "Оплачен"

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
        verbose_name="Статус",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    document = models.ImageField(
        upload_to="document/",
        null=True,
        blank=True,
        verbose_name="Чек / скриншот оплаты",
    )

    qr_url = models.URLField(blank=True, verbose_name="Ссылка на оплату")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")

    def save(self, *args, **kwargs):
        # Если документ загружен, и статус ещё "created" → ставим "check"
        if self.document and self.status == self.Status.CREATED:
            self.status = self.Status.CHECK
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Оплата бронирования"
        verbose_name_plural = "Оплаты бронирований"

    def __str__(self):
        return f"Оплата для брони №{self.booking.id}"


class Feedback(models.Model):
    """Модель хранения обратной связи"""

    email = models.EmailField(verbose_name="Email")
    message = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")

    class Meta:
        verbose_name = "Обратная связь"
        verbose_name_plural = "Обратная связь"

    def __str__(self):
        return f"Сообщение от {self.email}"
