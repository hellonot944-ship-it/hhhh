import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Core ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-secret-CHANGE-before-deploy")
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

# Auto-detect Railway / Render hostnames so you don't have to set
# DJANGO_ALLOWED_HOSTS manually on those platforms.
_ALLOWED = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]
# Railway injects RAILWAY_PUBLIC_DOMAIN
_railway = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
if _railway:
    _ALLOWED.append(_railway)
# Render injects RENDER_EXTERNAL_HOSTNAME
_render = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
if _render:
    _ALLOWED.append(_render)
# Always allow localhost for dev/health-check pings
_ALLOWED += ["localhost", "127.0.0.1"]
ALLOWED_HOSTS = list(dict.fromkeys(_ALLOWED))  # deduplicate, preserve order

# ─── Apps ────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

import os as _os
USE_CLOUDINARY = bool(_os.environ.get("CLOUDINARY_URL"))
if USE_CLOUDINARY:
    INSTALLED_APPS += ["cloudinary_storage", "cloudinary"]

INSTALLED_APPS += [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "accounts",
    "shop",
    "orders",
    "payments",
]

# ─── Middleware ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "lamlibaas_api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "lamlibaas_api.wsgi.application"

# ─── Database ─────────────────────────────────────────────────────────────────
# Railway/Render inject DATABASE_URL when Postgres is attached.
# Falls back to SQLite if not set or malformed (e.g. empty string).
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if DATABASE_URL and DATABASE_URL.startswith(("postgres://", "postgresql://", "postgis://")):
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)}
else:
    if DATABASE_URL:
        import logging
        logging.warning(f"DATABASE_URL is set but unrecognised ('{DATABASE_URL[:30]}...') — falling back to SQLite")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── Internationalisation ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True

# ─── Static & Media ───────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
if USE_CLOUDINARY:
    STORAGES["default"] = {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── DRF / JWT ────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Your Netlify frontend URL goes here. Comma-separated in env var.
# Default includes the Netlify preview domain pattern so new deploys work
# automatically — tighten this to your custom domain once you have one.
_CORS_RAW = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5500,http://127.0.0.1:5500"
)
CORS_ALLOWED_ORIGINS = [o.strip() for o in _CORS_RAW.split(",") if o.strip()]

# Allow all Netlify preview deploy URLs automatically (*.netlify.app)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.netlify\.app$",
]

CORS_ALLOW_CREDENTIALS = True

# ─── Frontend / Store ─────────────────────────────────────────────────────────
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
STORE_OWNER_EMAIL = os.environ.get("STORE_OWNER_EMAIL", "")

# ─── Payment methods ──────────────────────────────────────────────────────────
ENABLED_PAYMENT_METHODS = [m.strip() for m in os.environ.get(
    "ENABLED_PAYMENT_METHODS", "jazzcash,easypaisa,bank_transfer"
).split(",") if m.strip()]

BANK_TRANSFER_DETAILS = {
    "bank_name": os.environ.get("BANK_NAME", ""),
    "account_title": os.environ.get("BANK_ACCOUNT_TITLE", ""),
    "account_number": os.environ.get("BANK_ACCOUNT_NUMBER", ""),
    "iban": os.environ.get("BANK_IBAN", ""),
}

# ─── JazzCash ─────────────────────────────────────────────────────────────────
JAZZCASH_MODE = os.environ.get("JAZZCASH_MODE", "sandbox")
JAZZCASH_MERCHANT_ID = os.environ.get("JAZZCASH_MERCHANT_ID", "")
JAZZCASH_PASSWORD = os.environ.get("JAZZCASH_PASSWORD", "")
JAZZCASH_INTEGRITY_SALT = os.environ.get("JAZZCASH_INTEGRITY_SALT", "")
JAZZCASH_RETURN_URL = os.environ.get("JAZZCASH_RETURN_URL", f"{FRONTEND_URL}/order-tracking.html")

# ─── EasyPaisa ────────────────────────────────────────────────────────────────
EASYPAISA_MODE = os.environ.get("EASYPAISA_MODE", "sandbox")
EASYPAISA_STORE_ID = os.environ.get("EASYPAISA_STORE_ID", "")
EASYPAISA_HASH_KEY = os.environ.get("EASYPAISA_HASH_KEY", "")
EASYPAISA_RETURN_URL = os.environ.get("EASYPAISA_RETURN_URL", f"{FRONTEND_URL}/order-tracking.html")

# ─── Email ────────────────────────────────────────────────────────────────────
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
if EMAIL_HOST_USER:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    DEFAULT_FROM_EMAIL = "noreply@lamlibaas.com"

# ─── SMS (Twilio) ─────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")

# ─── Security (production only) ───────────────────────────────────────────────
# Only enable SSL redirect on real deployed hosts — not in test runner
# (tests use http://testserver which would 301 to https and break everything)
_is_deployed = bool(os.environ.get("DATABASE_URL") or os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"))
if not DEBUG and _is_deployed:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
