import datetime, logging
from decimal import Decimal
from django.apps import apps
from django.db import models
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html
from .config import APP_LABEL, DASHBOARD_CONFIG

logger = logging.getLogger(__name__)


def _normalize(s):
    return (s or "").lower().replace("_", "").replace(" ", "").replace("-", "")


def get_model(model_key):
    if not model_key or not isinstance(model_key, str):
        return None
    try:
        app_config = apps.get_app_config(APP_LABEL)
    except LookupError:
        logger.warning("App '%s' not found.", APP_LABEL)
        return None

    exact = {m._meta.model_name: m for m in app_config.get_models()}
    fuzzy = {_normalize(m._meta.model_name): m for m in app_config.get_models()}

    if model_key in exact: return exact[model_key]
    if model_key.lower() in exact: return exact[model_key.lower()]
    if _normalize(model_key) in fuzzy: return fuzzy[_normalize(model_key)]
    logger.warning("Model '%s' not found.", model_key)
    return None


def get_model_config(model_key):
    for cfg in DASHBOARD_CONFIG:
        if cfg["key"] == model_key or _normalize(cfg["key"]) == _normalize(model_key):
            return cfg
    return None


def _check(user, perm):
    try:
        return user.is_authenticated and user.has_perm(perm)
    except Exception:
        return False


def has_any_perm(user, key):
    return any(_check(user, f"{APP_LABEL}.{a}_{key}") for a in ("view", "add", "change", "delete"))
def has_view_perm(user, key): return _check(user, f"{APP_LABEL}.view_{key}")
def has_add_perm(user, key): return _check(user, f"{APP_LABEL}.add_{key}")
def has_change_perm(user, key): return _check(user, f"{APP_LABEL}.change_{key}")
def has_delete_perm(user, key): return _check(user, f"{APP_LABEL}.delete_{key}")


def is_staff_user(user):
    return bool(user.is_authenticated and (user.is_staff or user.is_superuser))


def is_student_user(user):
    return user.is_authenticated and not is_staff_user(user) and getattr(user, "category", None) == "STUDENT"


def get_student_engagement(user):
    try:
        return user.engagement_details
    except Exception:
        return None


def safe_count(model):
    try:
        return model.objects.count()
    except Exception:
        logger.exception("Count failed")
        return 0


def safe_queryset(model):
    try:
        qs = model.objects.all()
        fks = [f.name for f in model._meta.fields if f.is_relation and f.many_to_one]
        if fks: qs = qs.select_related(*fks)
        return qs
    except Exception:
        logger.exception("Query failed")
        return model.objects.none()


def get_concrete_fields(model, exclude=None):
    exclude = set(exclude or [])
    return [f for f in model._meta.fields if f.name not in exclude and f.concrete]


def format_field_value(obj, field):
    try:
        name = field.name
        if getattr(field, "choices", None):
            disp = getattr(obj, f"get_{name}_display", None)
            if disp: return str(disp() or "—")
        value = getattr(obj, name, None)
        if value is None or value == "": return "—"
        if isinstance(value, bool): return "✅ Yes" if value else "❌ No"
        if isinstance(field, (models.FileField, models.ImageField)):
            try: return format_html('<a href="{}" target="_blank">📎 Open</a>', value.url)
            except Exception: return "—"
        if isinstance(value, datetime.datetime): return value.strftime("%d %b %Y, %I:%M %p")
        if isinstance(value, datetime.date): return value.strftime("%d %b %Y")
        if isinstance(value, Decimal): return f"{value:.2f}"
        if field.is_relation: return str(value)
        s = str(value)
        return (s[:80] + "…") if len(s) > 80 else s
    except Exception:
        return "—"


def build_grouped_tables(model, group_by=None, exclude_fields=None, max_rows=300):
    try:
        fields = get_concrete_fields(model, exclude=exclude_fields)
        headers = [(f.verbose_name.title() if f.verbose_name else f.name) for f in fields]
        base_qs = safe_queryset(model)

        def _row(o): return {"pk": o.pk, "cells": [format_field_value(o, f) for f in fields]}

        if not group_by:
            total = base_qs.count()
            return [{"label": None, "count": total, "headers": headers, "rows": [_row(o) for o in base_qs[:max_rows]], "truncated": total > max_rows}]

        try:
            gfield = model._meta.get_field(group_by)
        except Exception:
            return build_grouped_tables(model, None, exclude_fields, max_rows)

        groups = []
        if getattr(gfield, "choices", None):
            for val, disp in gfield.choices:
                qs = base_qs.filter(**{group_by: val})
                groups.append({"label": disp, "count": qs.count(), "headers": headers, "rows": [_row(o) for o in qs[:max_rows]], "truncated": qs.count() > max_rows})
            return groups

        try:
            vals = base_qs.values_list(group_by, flat=True).distinct()
            for val in vals:
                label = str(val) if val not in (None, "") else "— (Empty)"
                qs = base_qs.filter(**{group_by: val})
                groups.append({"label": label, "count": qs.count(), "headers": headers, "rows": [_row(o) for o in qs[:max_rows]], "truncated": qs.count() > max_rows})
        except Exception:
            logger.exception("Plain grouping failed")
        return groups
    except Exception:
        logger.exception("build_grouped_tables failed")
        return []