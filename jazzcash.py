from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.order_create, name="order-create"),
    path("track/", views.order_track, name="order-track"),
]
