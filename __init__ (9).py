from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    size_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True)
    payment_method = serializers.ChoiceField(choices=["cod", "jazzcash", "easypaisa", "bank_transfer"], default="bank_transfer")
    coupon_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    shipping_full_name = serializers.CharField()
    shipping_phone = serializers.CharField()
    shipping_street = serializers.CharField()
    shipping_city = serializers.CharField()
    shipping_province = serializers.CharField(required=False, allow_blank=True)
    shipping_postal_code = serializers.CharField(required=False, allow_blank=True)

    guest_name = serializers.CharField(required=False, allow_blank=True)
    guest_email = serializers.CharField(required=False, allow_blank=True)
    guest_phone = serializers.CharField(required=False, allow_blank=True)


class OrderSerializer(serializers.ModelSerializer):
    has_payment_proof = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "status", "payment_method", "payment_status",
            "subtotal", "shipping_fee", "discount_amount", "total",
            "shipping_full_name", "shipping_phone", "shipping_city", "created_at",
            "has_payment_proof",
        ]

    def get_has_payment_proof(self, obj):
        return bool(obj.payment_proof)
