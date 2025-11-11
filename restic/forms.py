from django import forms
from .models import Booking, Table

class BookingCreateForm(forms.ModelForm):
    selected_tables = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    booking_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Дата бронирования"
    )
    booking_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        label="Время бронирования"
    )

    class Meta:
        model = Booking
        fields = ['booking_date', 'booking_time']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['selected_tables'].required = True

    def clean_selected_tables(self):
        raw = self.cleaned_data['selected_tables']
        try:
            table_numbers = [int(x.strip()) for x in raw.split(',') if x.strip()]
            if not table_numbers:
                raise forms.ValidationError("Выберите хотя бы один стол.")
            # Проверяем, существуют ли такие столы
            existing = Table.objects.filter(number__in=table_numbers, is_active=True)
            if len(existing) != len(table_numbers):
                raise forms.ValidationError("Один или несколько столов недоступны.")
            return table_numbers
        except ValueError:
            raise forms.ValidationError("Неверный формат списка столов.")

    def save(self, commit=True):
        booking = super().save(commit=False)
        if commit:
            booking.save()
            # Привязываем столы
            table_numbers = self.cleaned_data['selected_tables']
            tables = Table.objects.filter(number__in=table_numbers)
            booking.tables.set(tables)
        return booking