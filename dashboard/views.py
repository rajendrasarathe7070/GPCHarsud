import logging, json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Count

from .config import DASHBOARD_CONFIG
from .decorators import dashboard_login_required
from .forms import get_student_profile_form_class, get_student_engagement_form_class
from .utils import (
    get_model, get_model_config, safe_count, has_any_perm, has_view_perm, 
    is_staff_user, is_student_user, get_student_engagement, build_grouped_tables, 
    has_add_perm, has_change_perm, has_delete_perm
)
from .crud import build_model_form, style_form_fields

logger = logging.getLogger(__name__)

# ✅ 1. Router (Yeh missing tha jiski wajah se error aaya)
@dashboard_login_required
def dashboard_router(request):
    try:
        if is_staff_user(request.user):
            return redirect("dashboard:staff_dashboard")
        if is_student_user(request.user):
            return redirect("dashboard:student_dashboard")
        return render(request, "dashboard/permission_denied.html", status=403)
    except Exception:
        logger.exception("router failed")
        return render(request, "dashboard/dashboard_error.html", status=500)


# ✅ 2. Staff Dashboard (Analytics & Graphs)
@dashboard_login_required
@require_http_methods(["GET"])
def staff_dashboard(request):
    user = request.user
    if not is_staff_user(user):
        return render(request, "dashboard/permission_denied.html", status=403)

    try:
        SE = get_model("studentengagement")
        BP = get_model("branchplacement")
        U = get_model("customuser")
        N = get_model("notice")
        FS = get_model("feestructure")
        SYL = get_model("syllabus")

        total_students = U.objects.filter(category='STUDENT').count() if U else 0
        total_placed = SE.objects.filter(got_placement=True).count() if SE else 0
        higher_studies = SE.objects.filter(opted_for_higher_studies=True).count() if SE else 0
        entrepreneurship = SE.objects.filter(opted_for_entrepreneurship=True).count() if SE else 0

        # Branch Placements
        branches = BP.objects.all()[:6] if BP else []
        bar_labels = [b.branch_name for b in branches]
        bar_placed = [b.students_placed for b in branches]
        bar_total = [b.final_year_students for b in branches]

        # Users by Category
        users_by_cat = U.objects.values('category').annotate(count=Count('id')) if U else []
        cat_map = dict(U.CATEGORY_CHOICES) if U else {}
        users_labels = [cat_map.get(u['category'], u['category']) for u in users_by_cat]
        users_data = [u['count'] for u in users_by_cat]

        # Notices by Type
        notices_type = N.objects.values('notice_type').annotate(count=Count('id')) if N else []
        notice_map = dict(N.NOTICE_TYPES) if N else {}
        notice_labels = [notice_map.get(n['notice_type'], n['notice_type']) for n in notices_type]
        notice_data = [n['count'] for n in notices_type]

        # Fee Structure
        fee_freq = FS.objects.values('frequency').annotate(count=Count('id')) if FS else []
        fee_map = dict(FS.FREQUENCY_CHOICES) if FS else {}
        fee_labels = [fee_map.get(f['frequency'], f['frequency']) for f in fee_freq]
        fee_data = [f['count'] for f in fee_freq]

        # Syllabus
        syl_branch = SYL.objects.values('brach').annotate(count=Count('id')) if SYL else []
        syl_map = dict(SYL.braches) if SYL else {}
        syl_labels = [syl_map.get(s['brach'], s['brach']) for s in syl_branch]
        syl_data = [s['count'] for s in syl_branch]

        cards, total_records = [], 0
        for cfg in DASHBOARD_CONFIG:
            if has_any_perm(user, cfg["key"]):
                m = get_model(cfg["key"])
                if m:
                    c = safe_count(m)
                    total_records += c
                    cards.append({
                        **cfg, "count": c,
                        "url": reverse("dashboard:model_list", kwargs={"model_key": cfg["key"]}),
                    })

        return render(request, "dashboard/staff_dashboard.html", {
            "cards": cards,
            "total_records": total_records,
            "total_students": total_students,
            "total_placed": total_placed,
            "higher_studies": higher_studies,
            "entrepreneurship": entrepreneurship,
            "chart_donut_data": json.dumps([total_placed, higher_studies, entrepreneurship, 0]),
            "chart_bar_labels": json.dumps(bar_labels),
            "chart_bar_placed": json.dumps(bar_placed),
            "chart_bar_total": json.dumps(bar_total),
            "users_labels": json.dumps(users_labels),
            "users_data": json.dumps(users_data),
            "notice_labels": json.dumps(notice_labels),
            "notice_data": json.dumps(notice_data),
            "fee_labels": json.dumps(fee_labels),
            "fee_data": json.dumps(fee_data),
            "syl_labels": json.dumps(syl_labels),
            "syl_data": json.dumps(syl_data),
        })
    except Exception:
        logger.exception("staff_dashboard failed")
        return render(request, "dashboard/dashboard_error.html", status=500)


# ✅ 3. Student Dashboard
@dashboard_login_required
@require_http_methods(["GET"])
def student_dashboard(request):
    user = request.user
    if not is_student_user(user):
        return render(request, "dashboard/permission_denied.html", status=403)
    try:
        return render(request, "dashboard/student_dashboard.html", {
            "user": user, "engagement": get_student_engagement(user),
        })
    except Exception:
        logger.exception("student_dashboard failed")
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

        if request.method == "POST":
            p_form = ProfileForm(request.POST, request.FILES, instance=user)
            e_form = EngagementForm(request.POST, instance=engagement) if EngagementForm and engagement else None
            if p_form.is_valid() and (not e_form or e_form.is_valid()):
                with transaction.atomic():
                    p_form.save()
                    if e_form: e_form.save()
                messages.success(request, "Profile updated successfully ✅")
                return redirect("dashboard:student_dashboard")
            messages.error(request, "Please correct the errors below.")
        else:
            p_form = ProfileForm(instance=user)
            e_form = EngagementForm(instance=engagement) if EngagementForm and engagement else None

        return render(request, "dashboard/student_profile_edit.html", {
            "profile_form": p_form, "engagement_form": e_form,
        })
    except Exception:
        logger.exception("student_profile_edit failed")
        return render(request, "dashboard/dashboard_error.html", status=500)


# ✅ 4. Generic CRUD Operations
@dashboard_login_required
@require_http_methods(["GET"])
def model_list_view(request, model_key):
    try:
        cfg = get_model_config(model_key)
        if not cfg:
            return render(request, "dashboard/permission_denied.html", {"reason": "Model not configured."}, status=404)
        if not has_view_perm(request.user, model_key):
            return render(request, "dashboard/permission_denied.html", {"reason": "No permission."}, status=403)
        model = get_model(model_key)
        if not model:
            return render(request, "dashboard/permission_denied.html", status=404)

        groups = build_grouped_tables(model, cfg.get("group_by"), cfg.get("exclude_fields"))
        return render(request, "dashboard/model_list.html", {
            "cfg": cfg, "groups": groups, "model_key": model_key,
            "total": sum(g["count"] for g in groups),
            "can_add": has_add_perm(request.user, model_key),
            "can_change": has_change_perm(request.user, model_key),
            "can_delete": has_delete_perm(request.user, model_key),
        })
    except Exception:
        logger.exception("model_list_view failed")
        return render(request, "dashboard/dashboard_error.html", status=500)


@dashboard_login_required
@require_http_methods(["GET", "POST"])
def model_add_view(request, model_key):
    try:
        cfg = get_model_config(model_key)
        if not cfg or not has_add_perm(request.user, model_key):
            return render(request, "dashboard/permission_denied.html", status=403)
        model = get_model(model_key)
        FormClass = build_model_form(model, cfg.get("exclude_fields"))
        if not FormClass:
            return render(request, "dashboard/dashboard_error.html", status=500)

        if request.method == "POST":
            form = FormClass(request.POST, request.FILES)
            if form.is_valid():
                with transaction.atomic(): form.save()
                messages.success(request, "Created successfully ✅")
                return redirect("dashboard:model_list", model_key=model_key)
        else:
            form = FormClass()

        style_form_fields(form)
        return render(request, "dashboard/model_form.html", {
            "form": form, "cfg": cfg, "mode": "add", "model_key": model_key,
        })
    except Exception:
        logger.exception("model_add_view failed")
        return render(request, "dashboard/dashboard_error.html", status=500)


@dashboard_login_required
@require_http_methods(["GET", "POST"])
def model_edit_view(request, model_key, pk):
    try:
        cfg = get_model_config(model_key)
        if not cfg or not has_change_perm(request.user, model_key):
            return render(request, "dashboard/permission_denied.html", status=403)
        model = get_model(model_key)
        obj = get_object_or_404(model, pk=pk)
        FormClass = build_model_form(model, cfg.get("exclude_fields"))
        if not FormClass:
            return render(request, "dashboard/dashboard_error.html", status=500)

        if request.method == "POST":
            form = FormClass(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                with transaction.atomic(): form.save()
                messages.success(request, "Updated successfully ✅")
                return redirect("dashboard:model_list", model_key=model_key)
        else:
            form = FormClass(instance=obj)

        style_form_fields(form)
        return render(request, "dashboard/model_form.html", {
            "form": form, "cfg": cfg, "mode": "edit", "model_key": model_key, "object": obj,
        })
    except Exception:
        logger.exception("model_edit_view failed")
        return render(request, "dashboard/dashboard_error.html", status=500)


@dashboard_login_required
@require_http_methods(["GET", "POST"])
def model_delete_view(request, model_key, pk):
    try:
        cfg = get_model_config(model_key)
        if not cfg or not has_delete_perm(request.user, model_key):
            return render(request, "dashboard/permission_denied.html", status=403)
        model = get_model(model_key)
        obj = get_object_or_404(model, pk=pk)

        if request.method == "POST":
            with transaction.atomic(): obj.delete()
            messages.success(request, "Deleted successfully 🗑️")
            return redirect("dashboard:model_list", model_key=model_key)

        return render(request, "dashboard/model_confirm_delete.html", {
            "object": obj, "cfg": cfg, "model_key": model_key,
        })
    except Exception:
        logger.exception("model_delete_view failed")
        return render(request, "dashboard/dashboard_error.html", status=500)