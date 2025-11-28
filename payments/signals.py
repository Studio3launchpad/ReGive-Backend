from django.db.models.signals import post_save
from django.dispatch import receiver

from payments.models import Payment
from orders.models import Order
from notifications.models import Notification


#Update order status when payment is successful
@receiver(post_save, sender=Payment)
def update_order_after_payment(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.status == "SUCCESS":
        order = instance.order
        order.status = "PAID"
        order.save(update_fields=["status"])

        Notification.objects.create(
            user=order.buyer,
            title="Payment Successful",
            message=f"Your payment for order #{order.id} was successful."
        )

