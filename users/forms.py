import uuid

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.forms import ClearableFileInput
from django import forms

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

    def save(self, commit=True):
        '''Метод сохранения username (если в модели нет поля, то нужно использовать метод для записи
        т.к. AbstractUser всегда должен иметь username)'''
        user = super().save(commit=False)
        # Генерируем уникальный username из email или UUID
        if not user.username:
            # Вариант A: генерируем username из email (без @ и точки)
            # email_user = user.email.split('@')[0].replace('.', '_')
            # user.username = email_user[:150]  # обрезаем до лимита

            # Вариант B: генерируем username UUID (гарантированно уникальный)
            user.username = str(uuid.uuid4()).replace("-", "")[:150]

        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Ваш email"}),
        label="Email"
    )

    def clean_username(self):
        email = self.cleaned_data.get("username")
        if not User.objects.filter(email=email).exists():
            # Не раскрываем, что email не существует — для безопасности
            raise forms.ValidationError("Неверный email или пароль.")
        return email

    def confirm_login_allowed(self, user):
        # Если пользователь не активен (не подтвердил email)
        if not user.is_active:
            raise forms.ValidationError("Пожалуйста, подтвердите email, прежде чем войти.")
        return super().confirm_login_allowed(user)


class ImageWidget(ClearableFileInput):
    '''Специальный виджет для отображения фото в профиле'''
    template_name = 'users/widgets/image_widget.html'


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
        # Кастомный виджет для фото в профиле редактирования
        widgets = {
            'image': ImageWidget(),
        }

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
