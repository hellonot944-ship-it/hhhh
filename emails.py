from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("otp/request/", views.otp_request, name="otp-request"),
    path("otp/verify/", views.otp_verify, name="otp-verify"),
    path("me/", views.me, name="me"),
]
