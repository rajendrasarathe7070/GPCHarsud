import logging
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout

logger = logging.getLogger(__name__)
ADMIN_PREFIXES = ("/admin/",)

class AdminTwoFactorEnforceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            path = request.path_info
            user = getattr(request, "user", None)

            if (
                user and user.is_authenticated
                and any(path.startswith(p) for p in ADMIN_PREFIXES)
                and path not in ("/admin/login/", "/admin/logout/")
                and not request.session.get("otp_device_id")
                and not request.session.get("dashboard_2fa_verified")
            ):
                logger.warning("Blocking admin for %s", user.get_username())
                logout(request)
                return redirect("dashboard:login")
        except Exception:
            logger.exception("Admin middleware failed")
        return self.get_response(request)