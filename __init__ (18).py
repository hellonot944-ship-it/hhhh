import random
from django.db import models
from shop.models import Product, ProductSize, Coupon


STATUS_CHOICES = [
    ("pending", "Pending"), ("confirmed", "Confirmed"), ("packed", "Packed"),
    ("shipped", "Shipped"), ("delivered", "Delivered"), ("cancelled", "Cancelled"),
    ("returned", "Returned"),
]
# COD is kept as a model choice so it can be re-enabled later without a code/schema
# change — whether it's actually offered at checkout is controlled by the
# ENABLED_PAYMENT_METHODS setting (see settings.py / .env), not by removing it here.
PAYMENT_METHODS = [("cod", "Cash on Delivery"), ("jazzcash", "JazzCash"),
                    ("easypaisa", "EasyPaisa"), ("bank_transfer", "Bank Transfer")]
PAYMENT_STATUSES = [("unpaid", "Unpaid"), ("pending_review", "Pending Review"),
                     ("paid", "Paid"), ("refunded", "Refunded"), ("failed", "Failed")]


def generate_order_number():
    return f"LB-{random.randint(10000, 99999)}"


class Order(models.Model):
    order_number = models.CharField(max_length=20, unique=True, default=generate_order_number)
    user = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default="cod")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUSES, default="unpaid")

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)

    # Guest checkout is supported — these are always filled in even when `user` is set.
    guest_name = models.CharField(max_length=150, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)

    shipping_full_name = models.CharField(max_length=150)
    shipping_phone = models.CharField(max_length=20)
    shipping_street = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=100)
    shipping_province = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)

    notes = models.TextField(blank=True)
    gateway_txn_ref = models.CharField(max_length=64, blank=True, help_text="JazzCash/EasyPaisa transaction reference, set automatically.")
    payment_proof = models.ImageField(upload_to="payment_proofs/", null=True, blank=True,
                                       help_text="Bank transfer receipt screenshot, uploaded by the customer after checkout.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    size = models.ForeignKey(ProductSize, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} × {self.product}"
