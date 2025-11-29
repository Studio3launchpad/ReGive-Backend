from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from users.models import CustomUser, Profile

@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    """
    Automatically create a Profile whenever a new CustomUser is created.
    """
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_profile(sender, instance, **kwargs):
    """
    Save the user’s profile whenever the user object is saved.
    """
    instance.profile.save()

@receiver(pre_save, sender=CustomUser)
def set_superuser_defaults(sender, instance, **kwargs):
    """
    If the user is a superuser, enforce:
    - role = ADMIN
    - is_verified = True
    """
    if instance.is_superuser:
        instance.role = CustomUser.Roles.ADMIN
        instance.is_verified = True
