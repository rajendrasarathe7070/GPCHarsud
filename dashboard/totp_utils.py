import base64, io, logging, secrets
from datetime import timedelta
import pyotp, qrcode
from django.conf import settings
from django.utils import timezone
from .models import UserTOTP

logger = logging.getLogger(__name__)
ISSUER = getattr(settings, "DASHBOARD_TOTP_ISSUER", "Institute Admin")


def get_or_create_totp(user):
    try:
        obj, _ = UserTOTP.objects.get_or_create(user=user, defaults={"secret": pyotp.random_base32()})
        return obj
    except Exception:
        logger.exception("get_or_create_totp failed")
        return None


def get_qr_data_url(user, totp):
    try:
        uri = pyotp.TOTP(totp.secret).provisioning_uri(name=f"{ISSUER}:{user.get_username()}", issuer_name=ISSUER)
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(uri); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO(); img.save(buf, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}", uri
    except Exception:
        logger.exception("QR generation failed")
        return None, None


def verify_totp(user, code, window=1):
    try:
        code = (code or "").strip().replace(" ", "")
        if not code.isdigit() or len(code) != 6:
            return False, "Enter a valid 6-digit code."

        totp = get_or_create_totp(user)
        if not totp:
            return False, "Server error."

        if totp.is_locked():
            return False, "Too many failed attempts. Try after 15 minutes."

        if pyotp.TOTP(totp.secret).verify(code, valid_window=window):
            totp.register_success()
            return True, "OK"

        totp.register_failure()
        remaining = max(0, 5 - totp.failed_attempts)
        return False, f"Invalid code. {remaining} attempts left."
    except Exception:
        logger.exception("verify_totp failed")
        return False, "Verification error."


def enable_totp_for_user(user, code):
    try:
        ok, msg = verify_totp(user, code)
        if not ok:
            return False, msg, []
        totp = get_or_create_totp(user)
        if not totp:
            return False, "Server error", []
        if not totp.is_enabled:
            codes = [secrets.token_hex(4).upper() for _ in range(8)]
            totp.is_enabled = True
            totp.backup_codes = codes
            totp.save(update_fields=["is_enabled", "backup_codes"])
            return True, "2FA enabled successfully.", codes
        return True, "Already enabled.", totp.backup_codes
    except Exception:
        logger.exception("enable_totp_for_user failed")
        return False, "Enable failed.", []


def verify_any_2fa(user, code):
    """Verifies dashboard TOTP OR two_factor devices."""
    try:
        code = (code or "").strip().replace(" ", "")
        if not code:
            return False, "Code required.", None

        # 1. Dashboard TOTP
        try:
            totp = UserTOTP.objects.filter(user=user, is_enabled=True).first()
            if totp and pyotp.TOTP(totp.secret).verify(code, valid_window=1):
                totp.register_success()
                return True, "OK", "dashboard"
        except Exception:
            logger.exception("dashboard TOTP check failed")

        # 2. two_factor devices
        try:
            from django_otp import devices_for_user
            for dev in devices_for_user(user):
                if dev.confirmed and dev.verify_token(code):
                    return True, "OK", "two_factor"
        except Exception:
            pass

        return False, "Invalid code.", None
    except Exception:
        logger.exception("verify_any_2fa failed")
        return False, "Verification error.", None


def user_has_two_factor_2fa(user):
    try:
        from django_otp import devices_for_user
        return any(d.confirmed for d in devices_for_user(user))
    except Exception:
        return False


def user_has_dashboard_totp(user):
    try:
        return UserTOTP.objects.filter(user=user, is_enabled=True).exists()
    except Exception:
        return False


def user_has_any_2fa(user):
    return user_has_two_factor_2fa(user) or user_has_dashboard_totp(user)