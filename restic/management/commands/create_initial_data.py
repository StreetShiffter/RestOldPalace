from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from restic.models import Booking
import os

User = get_user_model()

class Command(BaseCommand):
    help = "Создаёт суперпользователя и группу 'Moderators'"

    def handle(self, *args, **options):
        admin_email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
        admin_password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")

        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                email=admin_email,
                password=admin_password,
            )
            self.stdout.write(self.style.SUCCESS(f"Суперпользователь {admin_email} создан"))
        else:
            self.stdout.write(f"Суперпользователь {admin_email} уже существует")

        group, created = Group.objects.get_or_create(name="Moderators")
        if created:
            self.stdout.write(self.style.SUCCESS("Группа 'Moderators' создана"))

            # (Опционально) Назначаем права группе
            # Например: право просматривать все бронирования
            try:
                content_type = ContentType.objects.get_for_model(Booking)
                permission = Permission.objects.get(
                    codename="view_all_bookings",  # ← должно быть объявлено в Meta.permissions модели Booking
                    content_type=content_type,
                )
                group.permissions.add(permission)
                self.stdout.write(
                    self.style.SUCCESS("Право 'view_all_bookings' назначено группе 'Moderators'")
                )
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING("Право 'view_all_bookings' не найдено. Убедитесь, что оно объявлено в модели.")
                )
        else:
            self.stdout.write("Группа 'Moderators' уже существует")
