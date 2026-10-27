import logging
from functools import wraps

from django.shortcuts import redirect
from django.urls import reverse

from .totp_utils import get_or_create_totp

logger = logging.getLogger(__name__)

SESSION_FLAG = "dashboard_2fa_verified"
TWO_FACTOR_VERIFIED_KEY = "otp_device_id"   # django-two-factor-auth sets this


def _two_factor_verified(request):
    """
    django-two-factor-auth ki verification check.
    Agar user ne /account/login/ se 2FA complete kiya hai
    → session me 'otp_device_id' hoga → True.
    """
    try:
        return bool(request.session.get(TWO_FACTOR_VERIFIED_KEY))
    except Exception:
        logger.exception("_two_factor_verified check failed")
        return False


def dashboard_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        try:
            # 1. Not logged in → /dashboard/login/
            if not request.user.is_authenticated:
                login_url = reverse("dashboard:login")
                return redirect(f"{login_url}?next={request.path}")

            # 2. Session already verified → allow
            if request.session.get(SESSION_FLAG):
                return view_func(request, *args, **kwargs)

            # 3. Came from two_factor login (otp_device_id in session) → trust
            if request.session.get(TWO_FACTOR_VERIFIED_KEY):
                request.session[SESSION_FLAG] = True
                request.session.pop("dashboard_2fa_skipped", None)
                logger.info(
                    "Auto-trusted %s via two_factor session", request.user
                )
                return view_func(request, *args, **kwargs)

            # 4. Has any 2FA (dashboard or two_factor) → ask to verify
            from .utils import user_has_any_2fa
            if user_has_any_2fa(request.user):
                return redirect("dashboard:totp_verify")

            # 5. No 2FA → setup/skip prompt
            return redirect("dashboard:totp_setup_prompt")
        except Exception:
            logger.exception("dashboard_login_required failed on %s", request.path)
            return redirect("dashboard:login")
    return _wrapped