from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "phone", "is_verified", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "password"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_phone(self, value):
        if value and User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("An account with this phone number already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        # username is required by AbstractUser — derive one from the email so
        # callers never need to supply it themselves.
        base_username = validated_data["email"].split("@")[0]
        username = base_username
        n = 1
        while User.objects.filter(username=username).exists():
            n += 1
            username = f"{base_username}{n}"
        user = User(username=username, **validated_data)
        user.set_password(password)
        user.save()
        return user


class AddressSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=50, default="Home")
    street = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=100)
    province = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    is_default = serializers.BooleanField(default=False)
