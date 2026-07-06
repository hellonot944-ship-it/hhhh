# Lamlibaas Backend (Django + DRF)

A real, working Django REST API matching the contract `public/js/api.js` in
the frontend already expects — products, orders, accounts, **and now real
payment methods for Pakistan (JazzCash, EasyPaisa, manual bank transfer)**,
persistent photo storage, real SMS OTP, and real email notifications.

**21 passing automated tests** (`python manage.py test`) — including the
JazzCash/EasyPaisa hash math, the bank-transfer-with-receipt-upload flow,
and email delivery, all verified against a live running server, not just
assumed correct.

## What's actually here

- `accounts/` — custom User (email + phone), JWT register/login, OTP login (real SMS via Twilio), addresses
- `shop/` — Category, Product (real photo uploads), ProductSize, Coupon, Wishlist, Contact
- `orders/` — Order + OrderItem, checkout + order tracking
- `payments/` — JazzCash + EasyPaisa gateway integration, bank transfer + receipt upload, payment-method toggle

## Payment methods — what's real vs what needs your action

| Method | Code status | What you still need to do |
|---|---|---|
| **Bank Transfer** | ✅ Fully working, no third party | Set your real `BANK_*` account details in `.env` |
| **JazzCash** | ✅ Code complete, hash verified against official docs | Apply for a JazzCash merchant account, plug in `JAZZCASH_*` credentials |
| **EasyPaisa** | ⚠️ Code complete but flagged — see `payments/gateways/easypaisa.py` | Same as above, **and** double-check the exact field order against the PDF EasyPaisa emails you (their docs aren't as standardized as JazzCash's) |
| **COD** | ✅ Model supports it, off by default | Add `cod` to `ENABLED_PAYMENT_METHODS` whenever you want it back — no code change |

**I cannot get you a JazzCash/EasyPaisa merchant account** — that's a KYC
process (business registration, NTN, bank account) only you can do,
usually through your bank or directly with JazzCash/EasyPaisa business
onboarding. Once you have credentials, it's purely an `.env` change.

## What's now real that wasn't before

- **Photos persist** — wire `CLOUDINARY_URL` (free tier, 2-minute signup at cloudinary.com) and uploaded product/receipt photos survive redeploys.
- **Real SMS** — wire `TWILIO_*` and OTP codes get actually texted instead of returned in the API response.
- **Real email** — wire `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` (Gmail App Password works) and order confirmations + contact form messages actually get emailed to you and the customer.
- **Bank transfer with proof upload** — customer transfers manually, uploads a receipt screenshot, order sits as `pending_review` until you check your bank statement and mark it paid in `/admin/`.

## Run it locally

```bash
cd lamlibaas-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver 8001
```

Open **http://127.0.0.1:8001/admin/** to add products/photos, view orders,
and manually mark bank transfers as paid after checking your statement.

## Deploying for real — full checklist

1. **Push to GitHub**, deploy `lamlibaas-backend` to **Railway** or **Render** (Netlify, where the frontend lives, can't run Django).
2. **Attach Postgres** — `DATABASE_URL` is auto-injected, no setup.
3. **Copy `.env.example` → set every value** you actually have right now (bank details first — that one's free and instant; leave gateway/SMS/email blank until you have those accounts).
4. **Cloudinary** (5 min, free): cloudinary.com → copy the `CLOUDINARY_URL` from your dashboard → set it as an env var. Do this before you upload your first real product photo, or it'll need re-uploading later.
5. **Gmail App Password** (2 min, free): myaccount.google.com/apppasswords → set `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`.
6. **Twilio** (5 min, free trial credit): twilio.com → buy/trial a number → set `TWILIO_*`. Until you do this, OTP login still works for testing (code comes back in the response) but doesn't text anyone real.
7. **JazzCash/EasyPaisa merchant accounts** — apply when you're ready to accept real mobile-wallet payments; this takes the longest (business KYC), do it in parallel with everything else.
8. **Update the frontend** — in `public/js/api.js`, change the production URL to your real Railway/Render domain, then redeploy on Netlify. That's the only frontend code change needed.
9. Run `python manage.py seed_demo` and `createsuperuser` once via your host's one-off shell command.

## Running tests

```bash
python manage.py test
```
