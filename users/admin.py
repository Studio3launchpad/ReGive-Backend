from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Address, Profile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    readonly_fields = ("date_joined", "last_login")

    list_display = (
        "id",
        "email",
        "full_name",
        "role",
        "is_verified",
        "is_active",
        "is_deleted",
        "date_joined",
    )

    list_filter = ("role", "is_verified", "is_active", "is_deleted")
    search_fields = ("email", "full_name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name",)}),
        ("Role & Status", {
            "fields": (
                "role",
                "is_verified",
                "is_active",
                "is_deleted",
                "is_staff",
                "is_superuser",
            )
        }),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "full_name",
                "role",
                "password1",
                "password2",
            ),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "birth_date")
    search_fields = ("user__email", "user__full_name", "phone_number")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "street", "city", "state", "country")
    search_fields = ("user__email", "street", "city")
    list_filter = ("city", "state", "country")