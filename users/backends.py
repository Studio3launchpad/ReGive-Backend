import re
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.exceptions import MultipleObjectsReturned


class EmailOrPhoneBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using either
    their email address or phone number.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

       
        identifier = username or kwargs.get("login") or kwargs.get(UserModel.USERNAME_FIELD)
        if not identifier or not password:
            return None

        
        normalized_phone = re.sub(r"\D", "", identifier)

        try:
            user = UserModel.objects.get(
                Q(email__iexact=identifier) | Q(phone_number=normalized_phone)
            )
        except UserModel.DoesNotExist:
            return None
        except MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user


