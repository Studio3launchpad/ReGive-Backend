from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from users.models import CustomUser, Profile



@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)



@receiver(post_save, sender=CustomUser)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()



@receiver(pre_save, sender=CustomUser)
def set_admin_defaults(sender, instance, **kwargs):
    """
    Ensure every superuser is:
    - role = ADMIN
    - is_verified = True
    """
    if instance.is_superuser:
        instance.role = CustomUser.Roles.ADMIN
        instance.is_verified = True
