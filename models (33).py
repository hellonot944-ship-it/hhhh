from django.urls import path
from . import views

urlpatterns = [
    path("methods/", views.payment_methods, name="payment-methods"),
    path("bank-details/", views.bank_details, name="bank-details"),
    path("bank-transfer/upload-proof/", views.bank_transfer_upload_proof, name="bank-transfer-upload-proof"),
    path("jazzcash/initiate/", views.jazzcash_initiate, name="jazzcash-initiate"),
    path("jazzcash/callback/", views.jazzcash_callback, name="jazzcash-callback"),
    path("easypaisa/initiate/", views.easypaisa_initiate, name="easypaisa-initiate"),
    path("easypaisa/callback/", views.easypaisa_callback, name="easypaisa-callback"),
]
