"""
JazzCash Page Redirection API (v1.1) integration.

Hashing scheme verified against JazzCash's own sandbox documentation and
the official Redirection-API sample code they distribute: every pp_ field
(excluding pp_SecureHash itself) is sorted alphabetically by key, the
values joined with '&', the Integrity Salt prepended with another '&',
and the result HMAC-SHA256'd using the Integrity Salt as the key — hex
digest, sent back as pp_SecureHash.

IMPORTANT: once your merchant account is approved, JazzCash sends you an
integration document — diff its field list against PP_FIELDS below before
going live. They occasionally add optional ppmpf_1..5 custom fields; this
implementation works fine without them, but include them here if your
account requires them.
"""
import hashlib
import hmac
from datetime import datetime, timedelta
from django.conf import settings


def _generate_secure_hash(fields: dict, integrity_salt: str) -> str:
    sorted_values = [str(fields[k]) for k in sorted(fields.keys()) if fields[k] not in (None, "")]
    to_be_hashed = integrity_salt + "&" + "&".join(sorted_values)
    return hmac.new(
        integrity_salt.encode("utf-8"),
        to_be_hashed.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def build_payment_request(order) -> dict:
    """Returns the full set of form fields (including pp_SecureHash) that
    must be auto-submitted via POST to JazzCash's transaction URL."""
    now = datetime.now()
    expiry = now + timedelta(hours=1)

    fields = {
        "pp_Version": "1.1",
        "pp_TxnType": "MWALLET",
        "pp_Language": "EN",
        "pp_MerchantID": settings.JAZZCASH_MERCHANT_ID,
        "pp_Password": settings.JAZZCASH_PASSWORD,
        "pp_TxnRefNo": f"T{order.order_number.replace('-', '')}{now.strftime('%H%M%S')}",
        "pp_Amount": str(int(order.total * 100)),  # paisas
        "pp_TxnCurrency": "PKR",
        "pp_TxnDateTime": now.strftime("%Y%m%d%H%M%S"),
        "pp_TxnExpiryDateTime": expiry.strftime("%Y%m%d%H%M%S"),
        "pp_BillReference": order.order_number,
        "pp_Description": f"Lamlibaas order {order.order_number}",
        "pp_ReturnURL": settings.JAZZCASH_RETURN_URL,
    }
    fields["pp_SecureHash"] = _generate_secure_hash(fields, settings.JAZZCASH_INTEGRITY_SALT)
    return fields


def verify_callback(data: dict) -> bool:
    """Verifies the pp_SecureHash JazzCash sends back to your return URL,
    to make sure the response wasn't tampered with in transit."""
    received_hash = data.get("pp_SecureHash", "")
    fields = {k: v for k, v in data.items() if k != "pp_SecureHash"}
    expected_hash = _generate_secure_hash(fields, settings.JAZZCASH_INTEGRITY_SALT)
    return hmac.compare_digest(received_hash.lower(), expected_hash.lower())


def get_transaction_url() -> str:
    if settings.JAZZCASH_MODE == "live":
        return "https://payments.jazzcash.com.pk/ApplicationAPI/API/Payment/DoTransaction"
    return "https://sandbox.jazzcash.com.pk/ApplicationAPI/API/Payment/DoTransaction"
