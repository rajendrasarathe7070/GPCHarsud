import base64
import io
import logging
import secrets

import pyotp
import qrcode
from django.conf import settings

from .models import UserTOTP

logger = logging.getLogger(__name__)



ISSUER = getattr(settings, "DASHBOARD_TOTP_ISSUER", "Institute Dashboard")


def get_or_create_totp(user):
    """Har user ke liye TOTP record ensure karta hai (secret ke saath)."""
    try:
        obj, created = UserTOTP.objects.get_or_create(
            user=user,
            defaults={"secret": pyotp.random_base32()},
        )
        return obj
    except Exception:
        logger.exception("get_or_create_totp failed for user=%s", getattr(user, "pk", "?"))
        return None


def get_totp_uri(user, totp):
    """Authenticator app ke liye otpauth:// URI."""
    label = f"{ISSUER}:{user.get_username()}"
    return pyotp.TOTP(totp.secret).provisioning_uri(name=label, issuer_name=ISSUER)


def get_qr_data_url(user, totp):
    """QR code ko base64 data URL me convert karta hai (template me <img src=...>)."""
    try:
        uri = get_totp_uri(user, totp)
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{b64}", uri
    except Exception:
        logger.exception("QR generation failed for user=%s", getattr(user, "pk", "?"))
        return None, None


def verify_totp(user, code, window=1):
    """
    Returns (ok: bool, message: str).
    window=1 → ±30s tolerance.
    """
    try:
        code = (code or "").strip().replace(" ", "")
        if not code.isdigit() or len(code) != 6:
            return False, "6-digit code daalein."

        totp = get_or_create_totp(user)
        if totp is None:
            return False, "Server error. Please retry."

        if totp.is_locked():
            return False, "Bahut zyada galat attempts. 15 min baad try karein."

        if pyotp.TOTP(totp.secret).verify(code, valid_window=window):
            totp.register_success()
            return True, "OK"

        totp.register_failure()
        return False, "Galat code. Dobara try karein."
    except Exception:
        logger.exception("verify_totp failed for user=%s", getattr(user, "pk", "?"))
        return False, "Verification error."


def enable_totp_for_user(user, code):
    """
    Setup ke time verify karke 2FA ko ON karta hai + backup codes generate karta hai.
    Returns (ok, message, backup_codes).
    """
    try:
        ok, msg = verify_totp(user, code)
        if not ok:
            return False, msg, []

        totp = get_or_create_totp(user)
        if totp is None:
            return False, "Server error", []

        if not totp.is_enabled:
            codes = [secrets.token_hex(4).upper() for _ in range(8)]
            totp.is_enabled = True
            totp.backup_codes = codes
            totp.save(update_fields=["is_enabled", "backup_codes"])
            return True, "2FA enabled successfully.", codes

        # Pehle se enabled
        return True, "2FA already enabled.", totp.backup_codes
    except Exception:
        logger.exception("enable_totp_for_user failed")
        return False, "Enable failed.", []


def disable_totp_for_user(user):
    try:
        UserTOTP.objects.filter(user=user).update(
            is_enabled=False, backup_codes=[], failed_attempts=0, locked_until=None
        )
        return True
    except Exception:
        logger.exception("disable_totp failed")
        return False
    
    
    
def verify_any_2fa(user, code):
    """
    Dashboard TOTP ya two_factor device — dono me se kisi se bhi verify ho sakta hai.
    Returns (ok: bool, message: str, method: str).
    method = 'dashboard' | 'two_factor' | None
    """
    try:
        code = (code or "").strip().replace(" ", "")
        if not code:
            return False, "Code daalein.", None

        # 1. Try dashboard TOTP first
        try:
            from .models import UserTOTP
            totp = UserTOTP.objects.filter(user=user, is_enabled=True).first()
            if totp and pyotp.TOTP(totp.secret).verify(code, valid_window=1):
                totp.register_success()
                return True, "OK", "dashboard"
            elif totp:
                # Failed — track but continue to two_factor
                totp.register_failure()
        except Exception:
            logger.exception("verify_any_2fa: dashboard path failed")

        # 2. Try two_factor devices
        try:
            from django_otp import devices_for_user
            for device in devices_for_user(user):
                if not device.confirmed:
                    continue
                try:
                    if device.verify_token(code):
                        return True, "OK", "two_factor"
                except Exception:
                    continue
        except Exception:
            logger.exception("verify_any_2fa: two_factor path failed")

        return False, "Galat code. Dobara try karein.", None
    except Exception:
        logger.exception("verify_any_2fa failed")
        return False, "Verification error.", None