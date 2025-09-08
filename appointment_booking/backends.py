from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import Patient

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = Patient.objects.get(email=email)
            if user.check_password(password):
                return user
        except get_user_model().DoesNotExist:
            return None
        