"""
Real email sending via Django's send_mail — works with any SMTP provider
(Gmail App Password, SendGrid, Mailgun, etc.) once EMAIL_HOST_* env vars
are set. Until then, EMAIL_BACKEND defaults to the console backend, which
just prints the email to the server log — nothing crashes, nothing is
silently lost, but no one actually receives anything. See backend README
for the 5-minute Gmail App Password setup.
"""
from django.conf import settings
from django.core.mail import send_mail


def send_order_confirmation(order):
    customer_email = order.guest_email
    if customer_email:
        send_mail(
            subject=f"Your Lamlibaas order {order.order_number} is confirmed",
            message=(
                f"Hi {order.shipping_full_name},\n\n"
                f"Thanks for your order! Order {order.order_number} — total Rs {order.total} "
                f"— is being prepared. Payment method: {order.get_payment_method_display()}.\n\n"
                f"Track it anytime at: {settings.FRONTEND_URL}/order-tracking.html?order={order.order_number}\n\n"
                f"— Lamlibaas"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer_email],
            fail_silently=True,
        )

    if settings.STORE_OWNER_EMAIL:
        send_mail(
            subject=f"🛍️ New order {order.order_number} — Rs {order.total}",
            message=(
                f"New order placed.\n\nOrder: {order.order_number}\nCustomer: {order.shipping_full_name} "
                f"({order.shipping_phone})\nAddress: {order.shipping_street}, {order.shipping_city}\n"
                f"Payment: {order.get_payment_method_display()}\nTotal: Rs {order.total}\n\n"
                f"View in admin: {settings.FRONTEND_URL.replace('https://', 'https://api.')}/admin/orders/order/{order.id}/change/"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.STORE_OWNER_EMAIL],
            fail_silently=True,
        )


def send_contact_notification(contact_message):
    if not settings.STORE_OWNER_EMAIL:
        return
    send_mail(
        subject=f"New contact form message from {contact_message.name}",
        message=f"From: {contact_message.name} ({contact_message.email})\n\n{contact_message.message}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.STORE_OWNER_EMAIL],
        fail_silently=True,
    )
