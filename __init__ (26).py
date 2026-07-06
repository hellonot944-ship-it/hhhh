import io
from decimal import Decimal
from django.test import TestCase, override_settings
from django.core import mail
from rest_framework.test import APIClient

from shop.models import Category, Product
from orders.models import Order
from payments.gateways import jazzcash, easypaisa


class JazzCashHashTests(TestCase):
    """Pure-function tests for the hashing math — no live JazzCash account
    needed. Confirms the hash is deterministic, sensitive to tampering,
    and that verify_callback() actually catches a modified field."""

    @override_settings(JAZZCASH_INTEGRITY_SALT="test-salt-123")
    def test_hash_is_deterministic(self):
        fields = {"pp_Amount": "100000", "pp_MerchantID": "MC123", "pp_TxnRefNo": "T1"}
        h1 = jazzcash._generate_secure_hash(fields, "test-salt-123")
        h2 = jazzcash._generate_secure_hash(fields, "test-salt-123")
        self.assertEqual(h1, h2)

    @override_settings(JAZZCASH_INTEGRITY_SALT="test-salt-123")
    def test_callback_verification_passes_for_untampered_data(self):
        fields = {"pp_Amount": "100000", "pp_BillReference": "LB-1", "pp_ResponseCode": "000"}
        fields["pp_SecureHash"] = jazzcash._generate_secure_hash(fields, "test-salt-123")
        self.assertTrue(jazzcash.verify_callback(fields))

    @override_settings(JAZZCASH_INTEGRITY_SALT="test-salt-123")
    def test_callback_verification_fails_if_tampered(self):
        fields = {"pp_Amount": "100000", "pp_BillReference": "LB-1", "pp_ResponseCode": "000"}
        fields["pp_SecureHash"] = jazzcash._generate_secure_hash(fields, "test-salt-123")
        fields["pp_Amount"] = "1"  # attacker changes the amount after the hash was generated
        self.assertFalse(jazzcash.verify_callback(fields))


class EasyPaisaHashTests(TestCase):
    def test_hash_changes_if_param_order_input_changes(self):
        fields = {"amount": "100.0", "storeId": "123", "orderRefNum": "LB-1",
                   "postBackURL": "https://x.com", "paymentMethod": "MA",
                   "autoRedirect": "1", "emailAddr": "", "mobileNum": "03001234567"}
        h1 = easypaisa._generate_hash(fields, "hashkey123")
        fields2 = dict(fields, amount="999.0")
        h2 = easypaisa._generate_hash(fields2, "hashkey123")
        self.assertNotEqual(h1, h2)


@override_settings(ENABLED_PAYMENT_METHODS=["jazzcash", "easypaisa", "bank_transfer"])
class PaymentMethodGatingTests(TestCase):
    """Confirms COD is actually rejected server-side when not enabled —
    this is the real toggle, not just a frontend UI choice."""

    def setUp(self):
        self.client = APIClient()
        cat = Category.objects.create(name="Stitched")
        self.product = Product.objects.create(name="Test", category=cat, price=Decimal("1000"))

    def _payload(self, method):
        return {
            "items": [{"product_id": self.product.id, "quantity": 1}],
            "payment_method": method,
            "shipping_full_name": "A", "shipping_phone": "03001234567",
            "shipping_street": "X", "shipping_city": "Lahore",
        }

    def test_cod_is_rejected_when_not_enabled(self):
        res = self.client.post("/api/v1/orders/create/", self._payload("cod"), format="json")
        self.assertEqual(res.status_code, 400)

    def test_bank_transfer_is_accepted(self):
        res = self.client.post("/api/v1/orders/create/", self._payload("bank_transfer"), format="json")
        self.assertEqual(res.status_code, 201)

    def test_payment_methods_endpoint_excludes_cod(self):
        res = self.client.get("/api/v1/payments/methods/")
        ids = [m["id"] for m in res.json()]
        self.assertNotIn("cod", ids)
        self.assertIn("bank_transfer", ids)


@override_settings(ENABLED_PAYMENT_METHODS=["bank_transfer"])
class BankTransferFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cat = Category.objects.create(name="Stitched")
        self.product = Product.objects.create(name="Test", category=cat, price=Decimal("1000"))
        res = self.client.post("/api/v1/orders/create/", {
            "items": [{"product_id": self.product.id, "quantity": 1}],
            "payment_method": "bank_transfer",
            "shipping_full_name": "A", "shipping_phone": "03001234567",
            "shipping_street": "X", "shipping_city": "Lahore",
        }, format="json")
        self.order_number = res.json()["order_number"]

    def test_bank_details_endpoint_works(self):
        res = self.client.get("/api/v1/payments/bank-details/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("account_number", res.json())

    def test_uploading_proof_marks_pending_review(self):
        fake_image = io.BytesIO(b"fake-image-bytes")
        fake_image.name = "receipt.jpg"
        res = self.client.post("/api/v1/payments/bank-transfer/upload-proof/", {
            "order_number": self.order_number, "proof": fake_image,
        }, format="multipart")
        self.assertEqual(res.status_code, 200)
        order = Order.objects.get(order_number=self.order_number)
        self.assertEqual(order.payment_status, "pending_review")
        self.assertTrue(order.payment_proof)

    def test_upload_without_file_is_rejected(self):
        res = self.client.post("/api/v1/payments/bank-transfer/upload-proof/", {
            "order_number": self.order_number,
        }, format="multipart")
        self.assertEqual(res.status_code, 400)


class EmailNotificationTests(TestCase):
    """Confirms order confirmation emails actually get sent (to Django's
    in-memory test backend) — proves the wiring works end-to-end, even
    though no real SMTP server is configured in this test environment."""

    @override_settings(ENABLED_PAYMENT_METHODS=["bank_transfer"], STORE_OWNER_EMAIL="owner@lamlibaas.com")
    def test_order_creation_sends_confirmation_emails(self):
        cat = Category.objects.create(name="Stitched")
        product = Product.objects.create(name="Test", category=cat, price=Decimal("1000"))
        client = APIClient()
        mail.outbox = []
        client.post("/api/v1/orders/create/", {
            "items": [{"product_id": product.id, "quantity": 1}],
            "payment_method": "bank_transfer", "guest_email": "customer@example.com",
            "shipping_full_name": "A", "shipping_phone": "03001234567",
            "shipping_street": "X", "shipping_city": "Lahore",
        }, format="json")
        self.assertEqual(len(mail.outbox), 2)  # one to customer, one to store owner
