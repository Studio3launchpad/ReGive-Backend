from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
import re


class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email or phone_number is the unique identifier
    for authentication instead of usernames.
    """

    def normalize_phone(self, phone_number: str) -> str:
        """
        Return a digits-only phone number string (or empty string if None).
        """
        return re.sub(r"\D", "", phone_number or "")

    def create_user(self, email, phone_number, full_name, password=None, **extra_fields):
        """
        Create and save a User with the given email and phone number.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        if not phone_number:
            raise ValueError(_("The phone number must be set"))

        email = self.normalize_email(email)
        phone_number = self.normalize_phone(phone_number)

        # Extract and remove 'role' from extra_fields to avoid duplication
        role = extra_fields.pop('role', self.model.Roles.BUYER)

        user = self.model(
            email=email,
            phone_number=phone_number,
            full_name=full_name,
            role=role,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone_number, full_name, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given credentials.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError(_("Superuser must have is_staff=True."))
        if not extra_fields.get("is_superuser"):
            raise ValueError(_("Superuser must have is_superuser=True."))

        phone_number = self.normalize_phone(phone_number)
        return self.create_user(email, phone_number, full_name, password, **extra_fields)

    def get_by_natural_key(self, identifier):
        """
        Allow login using either email or phone number.
        """
        return self.get(Q(email__iexact=identifier) | Q(phone_number=identifier))

