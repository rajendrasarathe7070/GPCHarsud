import logging, time
from django.contrib import messages
from django.contrib.auth import logout as auth_logout, login as auth_login, get_user_model
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_protect

from .decorators import SESSION_FLAG, PRE_2FA_USER_KEY
from .forms import DashboardLoginForm, TOTPVerifyForm, TOTPSetupForm
from .totp_utils import (
    get_or_create_totp, get_qr_data_url, verify_any_2fa, enable_totp_for_user,
    user_has_any_2fa, user_has_two_factor_2fa, user_has_dashboard_totp,
)

logger = logging.getLogger(__name__)
PRE_2FA_BACKEND_KEY = "pre_2fa_backend"
PRE_2FA_TS_KEY = "pre_2fa_created_at"
PRE_2FA_MAX_AGE = 600


def _save_pending_user(request, user, next_url=None):
    request.session[PRE_2FA_USER_KEY] = user.pk
    request.session[PRE_2FA_BACKEND_KEY] = getattr(user, "backend", "django.contrib.auth.backends.ModelBackend")
    request.session[PRE_2FA_TS_KEY] = time.time()
    if next_url: request.session["dashboard_next"] = next_url


def _get_pending_user(request):
    try:
        uid = request.session.get(PRE_2FA_USER_KEY)
        ts = request.session.get(PRE_2FA_TS_KEY)
        if not uid or not ts: return None, "no_pending"
        if time.time() - float(ts) > PRE_2FA_MAX_AGE:
            _clear_pending(request); return None, "expired"
        user = get_user_model().objects.filter(pk=uid, is_active=True).first()
        if not user: _clear_pending(request); return None, "user_gone"
        return user, None
    except Exception:
        logger.exception("_get_pending_user failed")
        return None, "error"


def _clear_pending(request):
    for k in (PRE_2FA_USER_KEY, PRE_2FA_BACKEND_KEY, PRE_2FA_TS_KEY):
        request.session.pop(k, None)


def _finalize_login(request, user):
    try:
        backend = request.session.pop(PRE_2FA_BACKEND_KEY, "django.contrib.auth.backends.ModelBackend")
        auth_login(request, user, backend=backend)
        _clear_pending(request)
        request.session[SESSION_FLAG] = True
        request.session.pop("dashboard_2fa_skipped", None)
        # Reset axes counter on successful 2FA
        try:
            from axes.utils import reset
            reset(username=user.get_username())
        except Exception:
            pass
    except Exception:
        logger.exception("_finalize_login failed")


def _fail_login(request):
    """Logout and force re-login — used when 2FA is cancelled."""
    try:
        request.session.flush()
        auth_logout(request)
    except Exception:
        logger.exception("_fail_login failed")


# ═══════ LOGIN ═══════
@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    try:
        if request.user.is_authenticated and request.session.get(SESSION_FLAG):
            return redirect("dashboard:router")

        if request.user.is_authenticated:
            _fail_login(request)
            return redirect("dashboard:login")

        next_url = request.GET.get("next") or request.POST.get("next") or "/dashboard/"

        if request.method == "POST":
            form = DashboardLoginForm(request.POST, request=request)
            if form.is_valid():
                user = form.user
                _save_pending_user(request, user, next_url=next_url)
                if user_has_any_2fa(user):
                    return redirect("dashboard:totp_verify")
                return redirect("dashboard:totp_setup_prompt")
        else:
            form = DashboardLoginForm()

        return render(request, "dashboard/auth/login.html", {"form": form, "next": next_url})
    except Exception:
        logger.exception("login_view failed")
        return render(request, "dashboard/dashboard_error.html", status=500)


@require_POST
def logout_view(request):
    try:
        _fail_login(request)
    except Exception:
        logger.exception("logout failed")
    return redirect("dashboard:login")


# ═══════ SETUP PROMPT — MANDATORY (no skip allowed) ═══════
@require_http_methods(["GET"])
def totp_setup_prompt(request):
    try:
        user, err = _get_pending_user(request)
        if not user:
            return redirect("dashboard:login")
        if user_has_any_2fa(user):
            return redirect("dashboard:totp_verify")
        return render(request, "dashboard/auth/setup_prompt.html", {"username": user.get_username()})
    except Exception:
        logger.exception("setup_prompt failed")
        return redirect("dashboard:login")


# Cancel = fail login (strict)
@require_POST
def totp_cancel(request):
    try:
        _fail_login(request)
        messages.error(request, "2FA is mandatory. Please complete setup to log in.")
        return redirect("dashboard:login")
    except Exception:
        logger.exception("totp_cancel failed")
        return redirect("dashboard:login")


# ═══════ SETUP ═══════
@require_http_methods(["GET", "POST"])
def totp_setup(request):
    try:
        user, err = _get_pending_user(request)
        if not user:
            return redirect("dashboard:login")
        if user_has_any_2fa(user):
            return redirect("dashboard:totp_verify")

        totp = get_or_create_totp(user)
        if not totp or totp.is_enabled:
            return redirect("dashboard:totp_verify")

        qr_url, uri = get_qr_data_url(user, totp)

        if request.method == "POST":
            form = TOTPSetupForm(request.POST)
            if form.is_valid():
                ok, msg, backup_codes = enable_totp_for_user(user, form.cleaned_data["code"])
                if ok:
                    _finalize_login(request, user)
                    return render(request, "dashboard/auth/setup_done.html", {"backup_codes": backup_codes})
                messages.error(request, msg)
        else:
            form = TOTPSetupForm()

        return render(request, "dashboard/auth/setup.html", {
            "form": form, "qr_data_url": qr_url, "secret": totp.secret, "uri": uri,
        })
    except Exception:
        logger.exception("totp_setup failed")
        return redirect("dashboard:login")


# ═══════ VERIFY ═══════
@require_http_methods(["GET", "POST"])
def totp_verify(request):
    try:
        if request.user.is_authenticated and request.session.get(SESSION_FLAG):
            return redirect("dashboard:router")

        user, err = _get_pending_user(request)
        if not user:
            if err == "expired":
                messages.error(request, "Session expired. Login again.")
            return redirect("dashboard:login")

        if not user_has_any_2fa(user):
            return redirect("dashboard:totp_setup_prompt")

        has_2fa = user_has_two_factor_2fa(user)
        has_dash = user_has_dashboard_totp(user)

        if request.method == "POST":
            form = TOTPVerifyForm(request.POST)
            if form.is_valid():
                ok, msg, method = verify_any_2fa(user, form.cleaned_data["code"])
                if ok:
                    _finalize_login(request, user)
                    nxt = request.session.pop("dashboard_next", "/dashboard/")
                    return redirect(nxt or "/dashboard/")
                messages.error(request, msg)
        else:
            form = TOTPVerifyForm()

        return render(request, "dashboard/auth/verify.html", {
            "form": form, "has_two_factor": has_2fa, "has_dashboard": has_dash,
        })
    except Exception:
        logger.exception("totp_verify failed")
        return redirect("dashboard:login")