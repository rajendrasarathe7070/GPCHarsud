import logging
from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)
SESSION_FLAG = "dashboard_2fa_verified"
PRE_2FA_USER_KEY = "pre_2fa_user_id"


def dashboard_login_required(view_func):
    """Strict 2FA — user must complete 2FA to access."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        try:
            # 1. Not logged in → login page
            if not request.user.is_authenticated:
                return redirect(f"{reverse('dashboard:login')}?next={request.path}")

            # 2. Logged in but 2FA not verified → verify/setup
            if not request.session.get(SESSION_FLAG):
                from .totp_utils import user_has_any_2fa
                if user_has_any_2fa(request.user):
                    return redirect("dashboard:totp_verify")
                return redirect("dashboard:totp_setup_prompt")

            return view_func(request, *args, **kwargs)
        except Exception:
            logger.exception("dashboard_login_required failed on %s", request.path)
            return redirect("dashboard:login")
    return _wrapped