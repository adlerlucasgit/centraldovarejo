from django.contrib import admin

from .models import Venda, ItemVenda


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "user",
        "date_time",
        "total",
        "payment_method",
    )

    list_filter = (
        "payment_method",
        "date_time",
    )

    search_fields = (
        "number",
        "user__username",
    )

    readonly_fields = (
        "date_time",
        "total",
    )

    inlines = [ItemVendaInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ItemVenda)
class ItemVendaAdmin(admin.ModelAdmin):
    list_display = (
        "sale",
        "product",
        "quantity",
        "unit_price",
        "subtotal",
    )

    readonly_fields = (
        "sale",
        "product",
        "quantity",
        "unit_price",
        "subtotal",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
