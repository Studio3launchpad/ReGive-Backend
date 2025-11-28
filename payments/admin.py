from django.contrib import admin

from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "amount", "provider", "status", "reference", "created_at")
    list_filter = ("provider", "status", "created_at")
    search_fields = ("order__id", "reference", "order__buyer__email")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    actions = ["mark_as_success", "mark_as_failed", "mark_as_refunded"]

    def mark_as_success(self, request, queryset):
        updated = queryset.update(status="SUCCESS")
        self.message_user(request, f"{updated} payment(s) marked as SUCCESS.")
    mark_as_success.short_description = "Mark selected payments as SUCCESS"

    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status="FAILED")
        self.message_user(request, f"{updated} payment(s) marked as FAILED.")
    mark_as_failed.short_description = "Mark selected payments as FAILED"

    def mark_as_refunded(self, request, queryset):
        updated = queryset.update(status="REFUNDED")
        self.message_user(request, f"{updated} payment(s) marked as REFUNDED.")
    mark_as_refunded.short_description = "Mark selected payments as REFUNDED"
