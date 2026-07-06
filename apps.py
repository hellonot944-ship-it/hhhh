from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address, OTPCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "phone", "first_name", "last_name", "is_verified", "is_staff", "date_joined")
    search_fields = ("email", "phone", "first_name", "last_name")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Lamlibaas profile", {"fields": ("phone", "is_verified")}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "city", "is_default")
    search_fields = ("user__email", "city")


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ("phone", "code", "is_used", "created_at")
    readonly_fields = ("phone", "code", "created_at")
