from django.contrib import admin
from .models import PaymentAttempt


@admin.register(PaymentAttempt)
class PaymentAttemptAdmin(admin.ModelAdmin):
    list_display = ("order", "gateway", "is_verified", "created_at")
    readonly_fields = ("order", "gateway", "request_payload", "callback_payload", "is_verified", "created_at")
