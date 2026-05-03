from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from .models import Cart, CartItem


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['book', 'quantity']
    can_delete = False


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ['user', 'item_count', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['user', 'created_at']
    inlines = [CartItemInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @display(description='Товарів')
    def item_count(self, obj):
        return obj.items.count()
