from django.contrib import admin
from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("first_name",
                    "last_name",
                    "city",
                    "email",
                    "phone",
                    "is_staff",
                    "image",)
    search_fields = (
        "date_joined",
        "email",
        "city",
    )
