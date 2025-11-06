from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r"^(\+7|8)\d{10}$",
    message="Телефон должен быть в формате: +79991234567 или 89991234567",
)
