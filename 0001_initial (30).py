"""
EasyPaisa hosted-checkout (Page Redirection) integration.

⚠️ Heads up — this one is the least standardized of the two gateways.
EasyPaisa's integration guide has changed across versions (v4.1/v4.2),
and different merchant packages get slightly different field sets. The
parameter order and HMAC-SHA256 scheme below match their most common
publicly-documented "POST Method" flow, but you MUST compare this against
the actual integration PDF EasyPaisa emails you when your merchant
account is approved — specifically check PARAM_ORDER below, since that
exact string is what gets hashed and a wrong order means every payment
fails signature verification.
"""
import hashlib
import hmac
from datetime import datetime, timedelta
from django.conf import settings

# This exact order matters — it's the order EasyPaisa concatenates fields
# in before hashing. Confirm against your own integration document.
PARAM_ORDER = ["amount", "autoRedirect", "emailAddr", "mobileNum", "orderRefNum", "paymentMethod", "postBackURL", "storeId"]


def _generate_hash(fields: dict, hash_key: str) -> str:
    to_be_hashed = "&".join(f"{k}={fields.get(k, '')}" for k in PARAM_ORDER)
    return hmac.new(hash_key.encode("utf-8"), to_be_hashed.encode("utf-8"), hashlib.sha256).hexdigest()


def build_payment_request(order) -> dict:
    """Returns the form fields to auto-submit (POST) to EasyPaisa's hosted
    checkout page."""
    expiry = datetime.now() + timedelta(hours=1)
    fields = {
        "amount": f"{order.total:.1f}",
        "autoRedirect": "1",
        "emailAddr": order.guest_email or "",
        "mobileNum": order.shipping_phone,
        "orderRefNum": order.order_number,
        "paymentMethod": "MA_PAYMENT_METHOD",  # mobile account; ask EasyPaisa support for the OTC/CC variants if needed
        "postBackURL": settings.EASYPAISA_RETURN_URL,
        "storeId": settings.EASYPAISA_STORE_ID,
        "expiryDate": expiry.strftime("%Y%m%d %H%M%S"),
    }
    fields["merchantHashedReq"] = _generate_hash(fields, settings.EASYPAISA_HASH_KEY)
    return fields


def verify_callback(data: dict) -> bool:
    """EasyPaisa's postback sends back status/desc/orderRefNum — there's no
    hash to re-verify on most merchant packages, so the recommended check
    is to independently confirm the order's status via their transaction
    inquiry API rather than trusting the postback fields alone. This stub
    does the minimal structural check; wire in the inquiry API call here
    once you have your merchant credentials."""
    return data.get("status") == "Success" and bool(data.get("orderRefNum"))


def get_checkout_url() -> str:
    if settings.EASYPAISA_MODE == "live":
        return "https://easypay.easypaisa.com.pk/easypay/Index.jsf"
    return "https://easypaystg.easypaisa.com.pk/easypay/Index.jsf"
