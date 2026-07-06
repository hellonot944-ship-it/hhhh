from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from orders.models import Order
from .models import PaymentAttempt
from .gateways import jazzcash, easypaisa


@api_view(["GET"])
@permission_classes([AllowAny])
def payment_methods(request):
    """The frontend calls this to know which payment methods to actually
    show at checkout — change ENABLED_PAYMENT_METHODS in your environment
    (no code change, no redeploy of code) to turn COD back on later."""
    labels = dict(Order._meta.get_field("payment_method").choices)
    return Response([
        {"id": pm, "label": labels.get(pm, pm)} for pm in settings.ENABLED_PAYMENT_METHODS
    ])


@api_view(["POST"])
@permission_classes([AllowAny])
def jazzcash_initiate(request):
    order = get_object_or_404(Order, order_number=request.data.get("order_number"))
    fields = jazzcash.build_payment_request(order)
    order.gateway_txn_ref = fields["pp_TxnRefNo"]
    order.save(update_fields=["gateway_txn_ref"])
    PaymentAttempt.objects.create(order=order, gateway="jazzcash", request_payload=fields)
    return Response({"action_url": jazzcash.get_transaction_url(), "fields": fields})


@api_view(["POST"])
@permission_classes([AllowAny])
def jazzcash_callback(request):
    data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
    order = Order.objects.filter(order_number=data.get("pp_BillReference")).first()
    verified = jazzcash.verify_callback(data)
    if order:
        PaymentAttempt.objects.filter(order=order, gateway="jazzcash").update(callback_payload=data, is_verified=verified)
        if verified and data.get("pp_ResponseCode") == "000":
            order.payment_status = "paid"
            order.status = "confirmed"
            order.save(update_fields=["payment_status", "status"])
        elif verified:
            order.payment_status = "failed"
            order.save(update_fields=["payment_status"])
    return Response({"received": True, "verified": verified})


@api_view(["POST"])
@permission_classes([AllowAny])
def easypaisa_initiate(request):
    order = get_object_or_404(Order, order_number=request.data.get("order_number"))
    fields = easypaisa.build_payment_request(order)
    PaymentAttempt.objects.create(order=order, gateway="easypaisa", request_payload=fields)
    return Response({"action_url": easypaisa.get_checkout_url(), "fields": fields})


@api_view(["POST"])
@permission_classes([AllowAny])
def easypaisa_callback(request):
    data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
    order = Order.objects.filter(order_number=data.get("orderRefNum")).first()
    verified = easypaisa.verify_callback(data)
    if order:
        PaymentAttempt.objects.filter(order=order, gateway="easypaisa").update(callback_payload=data, is_verified=verified)
        if verified:
            order.payment_status = "paid"
            order.status = "confirmed"
            order.save(update_fields=["payment_status", "status"])
    return Response({"received": True, "verified": verified})


@api_view(["POST"])
@permission_classes([AllowAny])
def bank_transfer_upload_proof(request):
    """Customer uploads a screenshot of their bank transfer receipt after
    placing a bank_transfer order. Order stays 'pending_review' until a
    human checks the bank statement and marks it paid in /admin/."""
    order = get_object_or_404(Order, order_number=request.data.get("order_number"))
    proof = request.FILES.get("proof")
    if not proof:
        return Response({"detail": "A receipt image (field name 'proof') is required."}, status=status.HTTP_400_BAD_REQUEST)
    order.payment_proof = proof
    order.payment_status = "pending_review"
    order.save(update_fields=["payment_proof", "payment_status"])
    return Response({"message": "Receipt received — we'll confirm your order once it's verified."})


@api_view(["GET"])
@permission_classes([AllowAny])
def bank_details(request):
    """Static bank account details shown at checkout for bank_transfer —
    set these via env vars, no code change needed to update them."""
    return Response({
        "bank_name": settings.BANK_TRANSFER_DETAILS["bank_name"],
        "account_title": settings.BANK_TRANSFER_DETAILS["account_title"],
        "account_number": settings.BANK_TRANSFER_DETAILS["account_number"],
        "iban": settings.BANK_TRANSFER_DETAILS["iban"],
    })
