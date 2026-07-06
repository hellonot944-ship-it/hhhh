"""
Sends OTP codes via Twilio when configured. Twilio works fine for sending
SMS to Pakistani numbers (+92) — sign up at twilio.com, buy/trial a number,
and set the three TWILIO_* env vars. Until those are set, this silently
falls back to "dev mode": no SMS is sent, and the OTP view returns the
code directly in the API response instead (clearly insecure for
production — see the warning that logs below).
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_sms(phone: str, code: str) -> bool:
    """Returns True if a real SMS was actually sent, False if running in
    dev-fallback mode (caller should still return the code in that case,
    for testing — see accounts/views.py otp_request)."""
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER):
        logger.warning("TWILIO_* not configured — OTP %s for %s was NOT texted. "
                        "Set TWILIO_ACCOUNT_SID/AUTH_TOKEN/FROM_NUMBER to send real SMS.", code, phone)
        return False

    from twilio.rest import Client
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    to_number = phone if phone.startswith("+") else f"+92{phone.lstrip('0')}"
    client.messages.create(
        body=f"Your Lamlibaas verification code is {code}. It expires in 10 minutes.",
        from_=settings.TWILIO_FROM_NUMBER,
        to=to_number,
    )
    return True
