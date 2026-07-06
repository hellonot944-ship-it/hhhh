from django.db import models


class PaymentAttempt(models.Model):
    """An audit log of every gateway initiation + callback, so you can
    debug a failed JazzCash/EasyPaisa payment without guessing."""
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="payment_attempts")
    gateway = models.CharField(max_length=20, choices=[("jazzcash", "JazzCash"), ("easypaisa", "EasyPaisa")])
    request_payload = models.JSONField(default=dict, blank=True)
    callback_payload = models.JSONField(default=dict, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gateway} — {self.order.order_number}"
