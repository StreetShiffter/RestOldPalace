from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from users.models import User  # Убедись, что модель импортирована
from users.validators import phone_validator


class CustomUserCreationForm(UserCreationForm):
    """Форма для регистрации пользователей"""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["first_name",
                  "last_name",
                  "email",
                  "phone",
                  "image",
                  "city",
                  "telegram_chat_id",
                  ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["first_name"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Фамилия:"}
        )

        self.fields["last_name"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Имя:"}
        )

        self.fields["email"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Почта пользователя:"}
        )

        self.fields["phone"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Номер телефона пользователя:"}
        )

        self.fields["image"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Фотография пользователя:"}
        )

        self.fields["city"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Город пользователя:"}
        )

        self.fields["telegram_chat_id"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Телеграм никнейм пользователя:"}
        )

    def clean(self):
        '''Используется для кросс-валидации нескольких полей'''
        pass

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone:
            try:
                phone_validator(phone)  # вызываем валидатор
            except ValidationError:
                raise forms.ValidationError(
                    "Телефон должен быть в формате: +79991234567 или 89991234567"
                )
        return phone

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError("Введите корректный email-адрес.")

            if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
                raise forms.ValidationError("Этот email уже используется.")
        return email

        # # Дополнительная проверка домена (опционально)
        # blocked_domains = ['mail.ru', 'disposable.com']
        # domain = email.split('@')[1]
        # if domain in blocked_domains:
        #     #     raise forms.ValidationError('Этот email-сервис не поддерживается.')
        # return email


class UserProfileForm(forms.ModelForm):
    """Форма для редактирования профиля (без смены пароля)"""

    class Meta:
        model = User
        fields = ["first_name",
                  "last_name",
                  "email",
                  "phone",
                  "image",
                  "city",
                  "telegram_chat_id",
                  ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["first_name"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Фамилия:"}
        )

        self.fields["last_name"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Имя:"}
        )

        self.fields["email"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Почта пользователя:"}
        )

        self.fields["phone"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Номер телефона пользователя:"}
        )

        self.fields["image"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Фотография пользователя:"}
        )

        self.fields["image"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Фотография пользователя:"}
        )

        self.fields["city"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Город пользователя:"}
        )

        self.fields["telegram_chat_id"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Телеграм никнейм пользователя:"}
        )

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone:
            try:
                phone_validator(phone)  # вызываем валидатор
            except ValidationError:
                raise forms.ValidationError(
                    "Телефон должен быть в формате: +79991234567 или 89991234567"
                )
        return phone

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError("Введите корректный email-адрес.")

            # Проверка уникальности email (кроме текущего пользователя)
            if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
                raise forms.ValidationError("Этот email уже используется.")
        return email
