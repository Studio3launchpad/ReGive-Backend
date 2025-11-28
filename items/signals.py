from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from items.models import Item, Category


# ✅ Generate unique slug for Category
@receiver(pre_save, sender=Category)
def category_slug(sender, instance, **kwargs):
    if not instance.slug:
        base = slugify(instance.name) or "category"
        slug = base
        counter = 1

        while Category.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base}-{counter}"
            counter += 1

        instance.slug = slug


# ✅ Generate unique slug for Item
@receiver(pre_save, sender=Item)
def item_slug(sender, instance, **kwargs):
    if not instance.slug:
        base = slugify(instance.name) or "item"
        slug = base
        counter = 1

        while Item.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base}-{counter}"
            counter += 1

        instance.slug = slug


# ✅ Ensure free items always have price = 0
@receiver(pre_save, sender=Item)
def enforce_free_price(sender, instance, **kwargs):
    if instance.is_free:
        instance.price = 0

