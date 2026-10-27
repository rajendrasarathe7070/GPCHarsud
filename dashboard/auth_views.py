import logging

from django.contrib import messages
from django.contrib.auth import logout as auth_logout, login as auth_login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods, require_POST

from .decorators import SESSION_FLAG
from .forms import DashboardLoginForm, TOTPVerifyForm, TOTPSetupForm
from .totp_utils import (
    get_or_create_totp, get_qr_data_url, verify_any_2fa, enable_totp_for_user,
)
from .utils import user_has_any_2fa, user_has_two_factor_2fa, user_has_dashboard_totp

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 1. LOGIN
# ──────────────────────────────────────────────
@require_http_methods(["GET", "POST"])
def login_view(request):
    try:
        # Already fully verified in this session → dashboard
        if request.user.is_authenticated and request.session.get(SESSION_FLAG):
            return redirect("dashboard:router")

        next_url = request.GET.get("next") or request.POST.get("next") or "/dashboard/"

        if request.method == "POST":
            form = DashboardLoginForm(request.POST, request=request)
            if form.is_valid():
                user = form.user
                auth_login(request, user)

                # 🧹 CRITICAL: clear ALL stale 2FA session keys
                for k in (SESSION_FLAG, "dashboard_2fa_skipped", "otp_device_id"):
                    request.session.pop(k, None)

                request.session["dashboard_next"] = next_url
                logger.info(
                    "Dashboard login: user=%s has_2fa=%s has_two_factor=%s has_dashboard_totp=%s",
                    user.get_username(),
                    user_has_any_2fa(user),
                    user_has_two_factor_2fa(user),
                    user_has_dashboard_totp(user),
                )

                # 🔀 Route based on what 2FA the user HAS
                if user_has_any_2fa(user):
                    return redirect("dashboard:totp_verify")

                # No 2FA → setup or skip prompt (fresh users)
                return redirect("dashboard:totp_setup_prompt")
        else:
            form = DashboardLoginForm()

        return render(request, "dashboard/login.html", {
            "form": form, "next": next_url,
        })
    except Exception:
        logger.exception("Dashboard login_view failed")
        return render(request, "dashboard/dashboard_error.html", status=500)


# ──────────────────────────────────────────────
# 2. LOGOUT
# ──────────────────────────────────────────────
@require_POST
def logout_view(request):
    try:
        request.session.flush()
    except Exception:
        logger.exception("Session flush failed")
    auth_logout(request)
    return redirect("dashboard:login")


# ──────────────────────────────────────────────
# 3. SETUP / SKIP PROMPT (only for users with NO 2FA)
# ──────────────────────────────────────────────
@login_required
@require_http_methods(["GET"])
def totp_setup_prompt(request):
    try:
        if request.session.get(SESSION_FLAG):
            return redirect("dashboard:router")

        # Agar user ke paas two_factor 2FA already hai → verify page pe bhejo
        if user_has_two_factor_2fa(request.user):
            messages.info(request, "Aapke paas 2FA already enabled hai. Verify karein.")
            return redirect("dashboard:totp_verify")

        # Agar dashboard TOTP already enabled hai → verify page
        if user_has_dashboard_totp(request.user):
            return redirect("dashboard:totp_verify")

        # Koi 2FA nahi → setup/skip prompt
        return render(request, "dashboard/totp_setup_prompt.html", {
            "username": request.user.get_username(),
        })
    except Exception:
        logger.exception("totp_setup_prompt failed")
        return render(request, "dashboard/dashboard_error.html", status=500)


@login_required
@require_POST
def totp_skip(request):
    try:
        request.session[SESSION_FLAG] = True
        request.session["dashboard_2fa_skipped"] = True
        messages.warning(
            request,
            "2FA skip kiya. Aap baad me enable kar sakte hain.",
        )
        return redirect("dashboard:router")
    except Exception:
        logger.exception("totp_skip failed")
        return render(request, "dashboard/dashboard_error.html", status=500)


# ──────────────────────────────────────────────
# 4. SETUP 2FA (only for users choosing "Setup" on the prompt)
# ──────────────────────────────────────────────
@login_required
@require_http_methods(["GET", "POST"])
def totp_setup(request):
    try:
        if request.session.get(SESSION_FLAG):
            return redirect("dashboard:router")

        # Already has 2FA? No need to setup dashboard TOTP
        if user_has_any_2fa(request.user):
            return redirect("dashboard:totp_verify")

        totp = get_or_create_totp(request.user)
        if totp is None:
            messages.error(
                request,
                "TOTP record create nahi ho paya. Admin se contact karein "
                "(migration run hui hai?).",
            )
            return redirect("dashboard:totp_setup_prompt")

        if totp.is_enabled:
            return redirect("dashboard:totp_verify")

        qr_data_url, uri = get_qr_data_url(request.user, totp)

        if request.method == "POST":
            form = TOTPSetupForm(request.POST)
            if form.is_valid():
                ok, msg, backup_codes = enable_totp_for_user(
                    request.user, form.cleaned_data["code"]
                )
                if ok:
                    request.session[SESSION_FLAG] = True
                    request.session.pop("dashboard_2fa_skipped", None)
                    messages.success(request, "2FA successfully enable ✅")
                    return render(request, "dashboard/totp_setup_done.html", {
                        "backup_codes": backup_codes,
                    })
                messages.error(request, msg)
        else:
            form = TOTPSetupForm()

        return render(request, "dashboard/totp_setup.html", {
            "form": form, "qr_data_url": qr_data_url,
            "secret": totp.secret, "uri": uri,
        })
    except Exception:
        logger.exception("totp_setup failed")
        return render(request, "dashboard/dashboard_error.html", status=500)


# ──────────────────────────────────────────────
# 5. VERIFY — handles BOTH dashboard TOTP + two_factor devices
# ──────────────────────────────────────────────
@login_required
@require_http_methods(["GET", "POST"])
def totp_verify(request):
    try:
        if request.session.get(SESSION_FLAG):
            return redirect("dashboard:router")

        # Koi 2FA nahi → setup prompt
        if not user_has_any_2fa(request.user):
            return redirect("dashboard:totp_setup_prompt")

        # Determine which methods available (for UI hint)
        has_two_factor = user_has_two_factor_2fa(request.user)
        has_dashboard = user_has_dashboard_totp(request.user)

        if request.method == "POST":
            form = TOTPVerifyForm(request.POST)
            if form.is_valid():
                ok, msg, method = verify_any_2fa(
                    request.user, form.cleaned_data["code"]
                )
                if ok:
                    request.session[SESSION_FLAG] = True
                    request.session.pop("dashboard_2fa_skipped", None)
                    logger.info(
                        "2FA verify success: user=%s method=%s",
                        request.user.get_username(), method,
                    )
                    nxt = request.session.pop("dashboard_next", "/dashboard/")
                    return redirect(nxt or "/dashboard/")
                messages.error(request, msg)
        else:
            form = TOTPVerifyForm()

        return render(request, "dashboard/totp_verify.html", {
            "form": form,
            "has_two_factor": has_two_factor,
            "has_dashboard": has_dashboard,
        })
    except Exception:
        logger.exception("totp_verify failed")
        return render(request, "dashboard/dashboard_error.html", status=500)