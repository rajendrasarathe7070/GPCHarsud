from django.shortcuts import render

# Create your views here.
import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from .crud import build_model_form, style_form_fields, form_has_file_fields

from .config import STUDENT_EXTRA_CARDS, PREVIEW_LIMIT
from .forms import get_student_profile_form_class, get_student_engagement_form_class
from .utils import (
    get_model, get_model_config, safe_count, safe_queryset,
    safe_admin_url, has_any_perm, has_view_perm, has_add_perm,
    has_change_perm, is_staff_user, is_student_user,
    get_student_engagement, build_grouped_tables, format_field_value,
    get_concrete_fields,
     has_delete_perm,
)
from .decorators import dashboard_login_required
logger = logging.getLogger(__name__)

from .crud import build_model_form, style_form_fields, form_has_file_fields
from .utils import has_delete_perm
# ───────── Router ─────────
@dashboard_login_required
def dashboard_router(request):
    try:
        if is_staff_user(request.user):
            return redirect("dashboard:staff_dashboard")
        if is_student_user(request.user):
            return redirect("dashboard:student_dashboard")
        return render(request, "dashboard/permission_denied.html", status=403)
    except Exception:
        logger.exception("Router failed for %s", request.user)
        return render(request, "dashboard/dashboard_error.html", status=500)


# ───────── STUDENT DASHBOARD ─────────
@dashboard_login_required
@require_http_methods(["GET"])
def student_dashboard(request):
    user = request.user
    if not is_student_user(user):
        return render(request, "dashboard/permission_denied.html", status=403)

    try:
        engagement = get_student_engagement(user)
        return render(request, "dashboard/student_dashboard.html", {
            "user": user,
            "engagement": engagement,
            "extra_cards": STUDENT_EXTRA_CARDS,
        })
    except Exception:
        logger.exception("Student dashboard error for %s", user)
        return render(request, "dashboard/dashboard_error.html", status=500)


@dashboard_login_required
@require_http_methods(["GET", "POST"])
def student_profile_edit(request):
    user = request.user
    if not is_student_user(user):
        return render(request, "dashboard/permission_denied.html", status=403)

    try:
        ProfileForm = get_student_profile_form_class()
        EngagementForm = get_student_engagement_form_class()
        engagement = get_student_engagement(user)

        profile_form = ProfileForm(request.POST or None, request.FILES or None, instance=user)
        engagement_form = None
        if EngagementForm and engagement:
            engagement_form = EngagementForm(
                request.POST or None, instance=engagement
            )

        if request.method == "POST":
            ok = profile_form.is_valid()
            if engagement_form is not None:
                ok = ok and engagement_form.is_valid()
            if ok:
                profile_form.save()
                if engagement_form is not None:
                    engagement_form.save()
                messages.success(request, "Profile updated successfully ✅")
                return redirect("dashboard:student_dashboard")
            messages.error(request, "Kripya errors theek karein.")

        return render(request, "dashboard/student_profile_edit.html", {
            "profile_form": profile_form,
            "engagement_form": engagement_form,
            "engagement": engagement,
        })
    except Exception:
        logger.exception("Student profile edit failed for %s", user)
        return render(request, "dashboard/dashboard_error.html", status=500)


# ───────── STAFF DASHBOARD ─────────
@dashboard_login_required
@require_http_methods(["GET"])
def staff_dashboard(request):
    user = request.user
    if not is_staff_user(user):
        return render(request, "dashboard/permission_denied.html", status=403)

    try:
        from .config import DASHBOARD_CONFIG
        cards = []
        for cfg in DASHBOARD_CONFIG:
            key = cfg["key"]
            if not has_any_perm(user, key):
                continue
            model = get_model(key)
            if model is None:
                continue
            cards.append({
                **cfg,
                "count": safe_count(model),
                "preview": list(safe_queryset(model).order_by("-pk")[:PREVIEW_LIMIT]),
                "url": f"/dashboard/model/{key}/",
            })

        groups = list(user.groups.values_list("name", flat=True))

        return render(request, "dashboard/staff_dashboard.html", {
            "cards": cards,
            "user_groups": groups,
            "total": len(cards),
        })
    except Exception:
        logger.exception("Staff dashboard failed for %s", user)
        return render(request, "dashboard/dashboard_error.html", status=500)


# ───────── GENERIC MODEL PAGE (per-model) ─────────
@dashboard_login_required
@require_http_methods(["GET"])
def model_list_view(request, model_key):
    user = request.user

    if not is_staff_user(user):
        return render(request, "dashboard/permission_denied.html", status=403)

    cfg = get_model_config(model_key)
    if cfg is None:
        return render(request, "dashboard/permission_denied.html", {"reason": "Model not configured."}, status=404)

    if not has_view_perm(user, model_key):
        return render(request, "dashboard/permission_denied.html", {
            "reason": f"Aapko '{cfg['label']}' dekhne ki permission nahi hai."
        }, status=403)

    model = get_model(model_key)
    if model is None:
        return render(request, "dashboard/permission_denied.html", status=404)

    try:
        groups = build_grouped_tables(
            model,
            group_by=cfg.get("group_by"),
            exclude_fields=cfg.get("exclude_fields") or [],
        )
        total = sum(g["count"] for g in groups) if groups else 0

        return render(request, "dashboard/model_list.html", {
            "cfg": cfg,
            "groups": groups,
            "total": total,
            "is_grouped": bool(cfg.get("group_by")),
            "model_key": model_key,
            "can_add": has_add_perm(user, model_key),
            "can_change": has_change_perm(user, model_key),
            "can_delete": has_delete_perm(user, model_key),
            "add_url": safe_admin_url(model_key, "add"),
            "admin_url": safe_admin_url(model_key, "changelist"),
        })
    except Exception:
        logger.exception("model_list_view failed for %s", model_key)
        return render(request, "dashboard/dashboard_error.html", status=500)
    
# ═══════════════════════════════════════════════════════════════
# CRUD: ADD
# ═══════════════════════════════════════════════════════════════
@dashboard_login_required
@require_http_methods(["GET", "POST"])
def model_add_view(request, model_key):
    user = request.user
    if not is_staff_user(user):
        return render(request, "dashboard/permission_denied.html", status=403)

    cfg = get_model_config(model_key)
    if cfg is None:
        return render(request, "dashboard/permission_denied.html", status=404)

    if not has_add_perm(user, model_key):
        return render(request, "dashboard/permission_denied.html",
                      {"reason": "Aapko is model me ADD karne ki permission nahi hai."},
                      status=403)

    model = get_model(model_key)
    if model is None:
        return render(request, "dashboard/permission_denied.html", status=404)

    try:
        FormClass = build_model_form(model, cfg.get("exclude_fields"))
        if FormClass is None:
            messages.error(request, "Form build nahi ho paya (admin se contact karein).")
            return redirect("dashboard:model_list", model_key=model_key)

        if request.method == "POST":
            form = FormClass(request.POST, request.FILES or None)
            if form.is_valid():
                try:
                    from django.db import transaction
                    with transaction.atomic():
                        obj = form.save()
                    messages.success(request, f"✅ Added: {obj}")
                    return redirect("dashboard:model_list", model_key=model_key)
                except Exception:
                    logger.exception("Save failed: %s", model_key)
                    messages.error(request, "Save karte waqt error aaya. Details server log me.")
        else:
            form = FormClass()

        style_form_fields(form)
        return render(request, "dashboard/model_form.html", {
            "cfg": cfg,
            "form": form,
            "mode": "add",
            "object": None,
            "has_files": form_has_file_fields(form),
            "model_key": model_key,
        })
    except Exception:
        logger.exception("model_add_view failed for %s", model_key)
        return render(request, "dashboard/dashboard_error.html", status=500)


# ═══════════════════════════════════════════════════════════════
# CRUD: EDIT
# ═══════════════════════════════════════════════════════════════
@dashboard_login_required
@require_http_methods(["GET", "POST"])
def model_edit_view(request, model_key, pk):
    user = request.user
    if not is_staff_user(user):
        return render(request, "dashboard/permission_denied.html", status=403)

    cfg = get_model_config(model_key)
    if cfg is None:
        return render(request, "dashboard/permission_denied.html", status=404)

    if not has_change_perm(user, model_key):
        return render(request, "dashboard/permission_denied.html",
                      {"reason": "Aapko is model me EDIT karne ki permission nahi hai."},
                      status=403)

    model = get_model(model_key)
    if model is None:
        return render(request, "dashboard/permission_denied.html", status=404)

    try:
        try:
            obj = model.objects.get(pk=pk)
        except model.DoesNotExist:
            messages.error(request, "Record mila nahi (delete ho gaya hoga).")
            return redirect("dashboard:model_list", model_key=model_key)

        FormClass = build_model_form(model, cfg.get("exclude_fields"))
        if FormClass is None:
            messages.error(request, "Form build nahi ho paya.")
            return redirect("dashboard:model_list", model_key=model_key)

        if request.method == "POST":
            form = FormClass(request.POST, request.FILES or None, instance=obj)
            if form.is_valid():
                try:
                    from django.db import transaction
                    with transaction.atomic():
                        updated = form.save()
                    messages.success(request, f"✅ Updated: {updated}")
                    return redirect("dashboard:model_list", model_key=model_key)
                except Exception:
                    logger.exception("Update failed: %s pk=%s", model_key, pk)
                    messages.error(request, "Update error. Details server log me.")
        else:
            form = FormClass(instance=obj)

        style_form_fields(form)
        return render(request, "dashboard/model_form.html", {
            "cfg": cfg,
            "form": form,
            "mode": "edit",
            "object": obj,
            "has_files": form_has_file_fields(form),
            "model_key": model_key,
        })
    except Exception:
        logger.exception("model_edit_view failed: %s pk=%s", model_key, pk)
        return render(request, "dashboard/dashboard_error.html", status=500)


# ═══════════════════════════════════════════════════════════════
# CRUD: DELETE
# ═══════════════════════════════════════════════════════════════
@dashboard_login_required
@require_http_methods(["GET", "POST"])
def model_delete_view(request, model_key, pk):
    user = request.user
    if not is_staff_user(user):
        return render(request, "dashboard/permission_denied.html", status=403)

    cfg = get_model_config(model_key)
    if cfg is None:
        return render(request, "dashboard/permission_denied.html", status=404)

    if not has_delete_perm(user, model_key):
        return render(request, "dashboard/permission_denied.html",
                      {"reason": "Aapko is model me DELETE karne ki permission nahi hai."},
                      status=403)

    model = get_model(model_key)
    if model is None:
        return render(request, "dashboard/permission_denied.html", status=404)

    try:
        try:
            obj = model.objects.get(pk=pk)
        except model.DoesNotExist:
            messages.warning(request, "Record pehle hi delete ho chuka hai.")
            return redirect("dashboard:model_list", model_key=model_key)

        if request.method == "POST":
            try:
                label = str(obj)
                from django.db import transaction
                with transaction.atomic():
                    obj.delete()
                messages.success(request, f"🗑️ Deleted: {label}")
                return redirect("dashboard:model_list", model_key=model_key)
            except Exception:
                logger.exception("Delete failed: %s pk=%s", model_key, pk)
                messages.error(request, "Delete error. Details server log me.")

        # GET → show confirmation
        return render(request, "dashboard/model_confirm_delete.html", {
            "cfg": cfg,
            "object": obj,
            "model_key": model_key,
        })
    except Exception:
        logger.exception("model_delete_view failed: %s pk=%s", model_key, pk)
        return render(request, "dashboard/dashboard_error.html", status=500)