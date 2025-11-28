from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from items.models import Item



class Cart(models.Model):
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts",
        verbose_name=_("Buyer"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Cart")
        verbose_name_plural = _("Carts")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Cart of {self.buyer}"

    @property
    def total_amount(self):
        """Calculate total cost of all items in the cart."""
        return sum(item.subtotal for item in self.items.all())



class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Cart"),
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name=_("Item"),
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Quantity"))

    class Meta:
        verbose_name = _("Cart Item")
        verbose_name_plural = _("Cart Items")
        unique_together = ("cart", "item")  

    def __str__(self):
        return f"{self.quantity} × {self.item.name}"

    @property
    def subtotal(self):
        """Calculate subtotal for this cart item."""
        return self.quantity * self.item.price
