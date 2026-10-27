import logging

from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)

# Kaunse paths admin-only enforce karenge
ADMIN_PATH_PREFIXES = ("/admin/",)
TWO_FACTOR_VERIFIED_KEY = "otp_device_id"


class AdminTwoFactorEnforceMiddleware:
    """
    /admin/ paths par sirf un users ko allow karta hai jinhone
    django-two-factor-auth ke through 2FA verify kiya hai.
    Dashboard-skip wale users ko /admin/ se block karta hai.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            path = request.path_info
            user = getattr(request, "user", None)

            if (
                user
                and user.is_authenticated
                and any(path.startswith(p) for p in ADMIN_PATH_PREFIXES)
                and path not in (
                    "/admin/login/",
                    "/admin/logout/",
                )
                and not request.session.get(TWO_FACTOR_VERIFIED_KEY)
            ):
                logger.warning(
                    "Blocking admin access for %s (no two_factor verification)",
                    user.get_username(),
                )
                # User ko admin logout karke two_factor login pe bhejo
                # (Django session flush)
                try:
                    from django.contrib.auth import logout as dj_logout
                    dj_logout(request)
                except Exception:
                    logger.exception("Admin force-logout failed")
                return redirect(reverse("two_factor:login"))

        except Exception:
            logger.exception("AdminTwoFactorEnforceMiddleware failed")

        return self.get_response(request)