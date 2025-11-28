from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("item", "quantity", "price")
    can_delete = False
    show_change_link = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "buyer",
        "colored_status",
        "total_amount_display",
        "created_at",
    )

    list_filter = (
        "status",
        ("buyer", admin.RelatedOnlyFieldListFilter),
        "created_at",
    )

    search_fields = (
        "id",
        "buyer__email",
        "buyer__full_name",
    )

    inlines = [OrderItemInline]

    readonly_fields = (
        "buyer",
        "shipping_address",
        "total_amount",
        "created_at",
    )

    fieldsets = (
        (_("Order Information"), {
            "fields": (
                "buyer",
                "shipping_address",
                "status",
            )
        }),
        (_("Financials"), {
            "fields": ("total_amount",)
        }),
        (_("Timestamps"), {
            "fields": ("created_at",)
        }),
    )

    ordering = ("-created_at",)

    
    STATUS_COLORS = {
        "PENDING": "orange",
        "PROCESSING": "blue",
        "SHIPPED": "purple",
        "DELIVERED": "green",
        "CANCELLED": "red",
    }

    def colored_status(self, obj):
        color = self.STATUS_COLORS.get(obj.status, "black")
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            color, obj.status
        )
    colored_status.short_description = "Status"

    
    def total_amount_display(self, obj):
        return f"₦{obj.total_amount:,.2f}"
    total_amount_display.short_description = "Total"

    actions = [
        "mark_processing",
        "mark_shipped",
        "mark_delivered",
        "mark_cancelled",
    ]

    def mark_processing(self, request, queryset):
        updated = queryset.update(status="PROCESSING")
        self.message_user(request, f"{updated} order(s) marked PROCESSING.")
    mark_processing.short_description = "Mark selected orders as PROCESSING"

    def mark_shipped(self, request, queryset):
        updated = queryset.update(status="SHIPPED")
        self.message_user(request, f"{updated} order(s) marked SHIPPED.")
    mark_shipped.short_description = "Mark selected orders as SHIPPED"

    def mark_delivered(self, request, queryset):
        updated = queryset.update(status="DELIVERED")
        self.message_user(request, f"{updated} order(s) marked DELIVERED.")
    mark_delivered.short_description = "Mark selected orders as DELIVERED"

    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status="CANCELLED")
        self.message_user(request, f"{updated} order(s) marked CANCELLED.")
    mark_cancelled.short_description = "Mark selected orders as CANCELLED"

