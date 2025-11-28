from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from orders.models import Order
from notifications.models import Notification



@receiver(pre_save, sender=Order)
def track_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def notify_order_event(sender, instance, created, **kwargs):

    # 1️⃣ Order created
    if created:
        Notification.objects.create(
            user=instance.buyer,
            title="Order Created",
            message=f"Your order #{instance.id} has been created and is now pending."
        )
        return

    # 2️⃣ Order status updated
    old_status = getattr(instance, "_old_status", None)

    if old_status and old_status != instance.status:
        Notification.objects.create(
            user=instance.buyer,
            title="Order Status Update",
            message=f"Your order #{instance.id} status changed from {old_status} to {instance.status}."
        )
