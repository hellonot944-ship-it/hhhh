from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTPCode
from .sms import send_otp_sms
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response({**_tokens_for(user), "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    identifier = request.data.get("email_or_phone", "")
    password = request.data.get("password", "")
    user = User.objects.filter(Q(email__iexact=identifier) | Q(phone=identifier)).first()
    if not user or not user.check_password(password):
        return Response({"detail": "Invalid email/phone or password."}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({**_tokens_for(user), "user": UserSerializer(user).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def otp_request(request):
    phone = request.data.get("phone", "")
    if not phone:
        return Response({"phone": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)
    otp = OTPCode.generate(phone)
    sms_sent = send_otp_sms(phone, otp.code)
    if sms_sent:
        return Response({"message": "OTP sent via SMS."})
    # Twilio isn't configured yet — fall back to returning the code directly
    # so login can still be tested end-to-end. Set TWILIO_* env vars to turn
    # this off and switch to real texted codes.
    return Response({"message": "OTP generated (SMS not configured — see backend README).", "code": otp.code})


@api_view(["POST"])
@permission_classes([AllowAny])
def otp_verify(request):
    phone = request.data.get("phone", "")
    code = request.data.get("code", "")
    otp = OTPCode.objects.filter(phone=phone, code=code).order_by("-created_at").first()
    if not otp or not otp.is_valid():
        return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)
    otp.is_used = True
    otp.save(update_fields=["is_used"])

    user, _ = User.objects.get_or_create(phone=phone, defaults={"username": f"user_{phone}", "is_verified": True})
    if not user.is_verified:
        user.is_verified = True
        user.save(update_fields=["is_verified"])
    return Response({**_tokens_for(user), "user": UserSerializer(user).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)
