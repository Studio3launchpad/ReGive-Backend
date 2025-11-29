from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import Notification


#Placeholder for push notifications (FCM, OneSignal, etc.)
@receiver(post_save, sender=Notification)
def send_push_notification(sender, instance, created, **kwargs):
    if created:
        #integrate FCM / OneSignal here
        pass

