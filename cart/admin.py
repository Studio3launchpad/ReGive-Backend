from django.contrib import admin
from .models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id"]  
    search_fields = ["id"]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["id", "cart", "item", "quantity"]  
    search_fields = ["cart__id", "item__name"]
    list_filter = ["cart"]  
    ordering = ["id"]  
    readonly_fields = []  


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = []  
