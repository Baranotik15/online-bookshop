from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from proj.admin_mixins import SuperuserEditMixin
from .models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['book', 'quantity', 'price']
    can_delete = False


@admin.register(Order)
class OrderAdmin(SuperuserEditMixin, ModelAdmin):
    list_display = ['id', 'user', 'total_price', 'display_status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['user', 'total_price', 'stripe_session_id', 'created_at']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Замовлення', {'fields': ('user', ('total_price', 'status'))}),
        ('Stripe', {'classes': ('collapse',), 'fields': ('stripe_session_id',)}),
        ('Дати', {'classes': ('collapse',), 'fields': ('created_at',)}),
    )

    @display(description='Статус', label={
        'pending':   'warning',
        'paid':      'success',
        'shipped':   'info',
        'cancelled': 'danger',
    })
    def display_status(self, obj):
        return obj.status
