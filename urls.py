import random
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """Custom user — adds a unique phone number, used for OTP login and
    as an alternate identifier alongside email (frontend lets people log
    in with either)."""
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.email or self.phone or self.username


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=50, default="Home")
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.label} — {self.street}, {self.city}"


class OTPCode(models.Model):
    """Stores OTP codes for phone login. No SMS gateway is connected yet —
    see README — so during development/testing the code is returned
    directly in the API response instead of being texted out."""
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def generate(cls, phone):
        code = f"{random.randint(0, 999999):06d}"
        return cls.objects.create(phone=phone, code=code)

    def is_valid(self):
        return not self.is_used and timezone.now() - self.created_at < timedelta(minutes=10)

    def __str__(self):
        return f"{self.phone} — {self.code}"
