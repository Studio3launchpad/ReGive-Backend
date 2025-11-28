from django.contrib import admin
from .models import Item, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "seller",
        "category",
        "price",
        "is_free",
        "condition",
        "status",
        "stock",
        "location",
        "created_at",
    )

    list_filter = (
        "condition",
        "status",
        "is_free",
        "category",
        ("seller", admin.RelatedOnlyFieldListFilter),
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "location",
        "seller__email",
        "category__name",
    )

    ordering = ("-created_at",)
    list_per_page = 25
