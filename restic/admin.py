from django.contrib import admin
from .models import Table, Booking, Feedback, Payment


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'capacity', 'price', 'is_active')
    list_filter = ('capacity', 'is_active')
    search_fields = ('number',)
    list_editable = ('is_active',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'tables_list',
        'booking_date',
        'booking_time',
        'booking_period',
        'total_amount',
        'screenshot',
        'created_at',
        'updated_at',
        'is_cancelled',
        'cancelled_at',
    )
    list_filter = ('created_at', 'booking_date')
    search_fields = ('user','booking_date',)
    filter_horizontal = ('tables',)  # удобный виджет для ManyToMany
    readonly_fields = ('total_amount', 'created_at', 'updated_at','cancelled_at')
    fieldsets = (
        ('Клиент', {
            'fields': ('user',)
        }),
        ('Бронирование', {
            'fields': ('tables', 'booking_date', 'booking_time', 'booking_period')
        }),
        ('Оплата и файлы', {
            'fields': ('total_amount', 'screenshot')
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Кастомные методы для отображения в list_display
    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    user_full_name.short_description = 'Клиент'
    user_full_name.admin_order_field = 'user__first_name'

    def formatted_reservation_datetime(self, obj):
        return f"{obj.reservation_date} {obj.reservation_time}"
    formatted_reservation_datetime.short_description = 'Дата и время брони'

    def tables_list(self, obj):
        return ", ".join([str(table) for table in obj.tables.all()])
    tables_list.short_description = 'Столики'

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Теперь можно обновить total_amount
        obj = form.instance
        total = sum(table.price for table in obj.tables.all())
        if obj.total_amount != total:
            obj.total_amount = total
            obj.save(update_fields=['total_amount'])


@admin.action(description="Пометить как прочитанные")
def mark_as_read(modeladmin, request, queryset):
    queryset.update(is_read=True)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('email', 'message', 'created_at')
    readonly_fields = ('created_at',)
    actions = [mark_as_read]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('status', 'booking', 'amount', 'document')
    readonly_fields = ('created_at',)
    actions = [mark_as_read]
