from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save
from django.dispatch import receiver

from users.models import CustomUser



class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Category Name"))
    slug = models.SlugField(max_length=60, unique=True, blank=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name



class Item(models.Model):

    CONDITION_CHOICES = (
        ("NEW", _("New")),
        ("USED", _("Used")),
        ("REFURBISHED", _("Refurbished")),
    )

    STATUS_CHOICES = (
        ("PUBLISHED", "Published"),
        ("DRAFT", "Draft"),
        ("SOLD", "Sold"),
        ("PENDING", "Pending"),
    )

    seller = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Seller"),
    )

    name = models.CharField(max_length=100, verbose_name=_("Item Name"))
    slug = models.SlugField(max_length=120, unique=True, blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="items",
        verbose_name=_("Category"),
    )

    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default="NEW",
        verbose_name=_("Condition"),
    )

    is_free = models.BooleanField(default=False, verbose_name=_("Free Item?"))

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=0.00,
        verbose_name=_("Price"),
    )

    is_negotiable = models.BooleanField(default=False)
    stock = models.PositiveIntegerField(default=1)

    location = models.CharField(max_length=100, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PUBLISHED",
    )

   
    image = models.ImageField(
        upload_to="item_images/",
        null=True,
        blank=True,
    )

    video = models.FileField(
        upload_to="item_videos/",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.is_free:
            self.price = 0.00
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class ItemReview(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    reviewer = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
    )
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Item Review")
        verbose_name_plural = _("Item Reviews")
        ordering = ["-created_at"]

    def __str__(self):
        reviewer = self.reviewer.full_name if self.reviewer else "Anonymous"
        return f"Review by {reviewer} on {self.item.name}"


@receiver(pre_save, sender=Category)
def generate_category_slug(sender, instance, **kwargs):
    if not instance.slug:
        base = slugify(instance.name) or "category"
        slug = base
        counter = 1

        while Category.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base}-{counter}"
            counter += 1

        instance.slug = slug


@receiver(pre_save, sender=Item)
def generate_item_slug(sender, instance, **kwargs):
    if not instance.slug:
        base = slugify(instance.name) or "item"
        slug = base
        counter = 1

        while Item.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base}-{counter}"
            counter += 1

        instance.slug = slug
