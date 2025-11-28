from django.contrib import admin

from wishlist.models import Wishlist


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "item", "added_at")
    list_filter = ("added_at",)
    search_fields = ("user__email", "user__full_name", "item__name")
    ordering = ("-added_at",)

