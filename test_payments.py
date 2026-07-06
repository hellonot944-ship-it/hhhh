from decimal import Decimal
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from shop.models import Product, ProductSize, Coupon
from lamlibaas_api.emails import send_order_confirmation
from .models import Order, OrderItem
from .serializers import OrderCreateSerializer, OrderSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def order_create(request):
    serializer = OrderCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if data["payment_method"] not in settings.ENABLED_PAYMENT_METHODS:
        return Response(
            {"payment_method": f"'{data['payment_method']}' is currently unavailable. "
                                f"Available methods: {', '.join(settings.ENABLED_PAYMENT_METHODS)}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    items_data = data["items"]
    products = {p.id: p for p in Product.objects.filter(id__in=[i["product_id"] for i in items_data])}
    missing = [i["product_id"] for i in items_data if i["product_id"] not in products]
    if missing:
        return Response({"detail": f"Unknown product id(s): {missing}"}, status=status.HTTP_400_BAD_REQUEST)

    subtotal = sum(products[i["product_id"]].price * i["quantity"] for i in items_data)
    shipping_fee = Decimal("0") if subtotal == 0 or subtotal >= 4000 else Decimal("200")

    discount_amount = Decimal("0")
    coupon = None
    coupon_code = data.get("coupon_code")
    if coupon_code:
        coupon = Coupon.objects.filter(code__iexact=coupon_code, is_active=True).first()
        if coupon and subtotal >= coupon.min_subtotal:
            discount_amount = Decimal(str(coupon.compute_discount(subtotal)))

    total = subtotal + shipping_fee - discount_amount

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        payment_method=data["payment_method"],
        coupon=coupon,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        discount_amount=discount_amount,
        total=total,
        guest_name=data.get("guest_name", ""),
        guest_email=data.get("guest_email", ""),
        guest_phone=data.get("guest_phone", ""),
        shipping_full_name=data["shipping_full_name"],
        shipping_phone=data["shipping_phone"],
        shipping_street=data["shipping_street"],
        shipping_city=data["shipping_city"],
        shipping_province=data.get("shipping_province", ""),
        shipping_postal_code=data.get("shipping_postal_code", ""),
    )

    for item in items_data:
        product = products[item["product_id"]]
        size = ProductSize.objects.filter(id=item.get("size_id")).first() if item.get("size_id") else None
        OrderItem.objects.create(order=order, product=product, size=size, quantity=item["quantity"], unit_price=product.price)

    send_order_confirmation(order)
    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([AllowAny])
def order_track(request):
    order_number = request.query_params.get("order_number", "")
    phone = request.query_params.get("phone", "")
    order = Order.objects.filter(order_number__iexact=order_number).first()
    if not order:
        return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
    valid_phones = {order.shipping_phone, order.guest_phone}
    if phone and phone not in valid_phones:
        return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(OrderSerializer(order).data)
