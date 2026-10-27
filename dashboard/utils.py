import datetime
import logging
from decimal import Decimal

from django.apps import apps
from django.db import models, DatabaseError
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html

from .config import APP_LABEL, DASHBOARD_CONFIG

logger = logging.getLogger(__name__)


# ────────── Model & Config helpers ──────────
def get_model(model_key):
    """
    App registry se model safely fetch karta hai.
    Multiple naam variations try karta hai (case-insensitive + underscore variants).
    """
    if not model_key:
        return None

    # Try variations: as-is, lowercase, no underscore, with underscore
    variants = {
        model_key,
        model_key.lower(),
        model_key.replace("_", ""),
        model_key.replace(" ", "_").lower(),
    }

    # Agar key me underscore hai → bina underscore wala bhi try karo
    # Agar bina underscore hai → underscore insert karke bhi try karo
    # (simple heuristic: check karo kya app me koi model match karta hai)

    try:
        app_config = apps.get_app_config(APP_LABEL)
    except LookupError:
        logger.warning("App '%s' not found in INSTALLED_APPS", APP_LABEL)
        return None
    except Exception:
        logger.exception("Error fetching app config '%s'", APP_LABEL)
        return None

    # Build a mapping of {lowercased_model_name: model}
    available = {
        m._meta.model_name.lower(): m for m in app_config.get_models()
    }

    for v in variants:
        if v in available:
            return available[v]

    # Nothing matched
    logger.warning(
        "Model '%s' not found in app '%s'. Available: %s",
        model_key, APP_LABEL, sorted(available.keys()),
    )
    return None


def get_model_config(model_key):
    for cfg in DASHBOARD_CONFIG:
        if cfg["key"] == model_key:
            return cfg
    return None


def get_configured_models():
    """List of (config, model_class) for all valid configured models."""
    out = []
    for cfg in DASHBOARD_CONFIG:
        m = get_model(cfg["key"])
        if m is not None:
            out.append((cfg, m))
    return out


# ────────── Permission checks ──────────
def _check(user, perm):
    try:
        return user.is_authenticated and user.has_perm(perm)
    except Exception:
        logger.exception("Permission check failed: %s", perm)
        return False


def has_any_perm(user, model_key):
    return any(
        _check(user, f"{APP_LABEL}.{action}_{model_key}")
        for action in ("view", "add", "change", "delete")
    )


def has_view_perm(user, model_key):
    return _check(user, f"{APP_LABEL}.view_{model_key}")


def has_add_perm(user, model_key):
    return _check(user, f"{APP_LABEL}.add_{model_key}")


def has_change_perm(user, model_key):
    return _check(user, f"{APP_LABEL}.change_{model_key}")

def has_delete_perm(user, model_key):
    return _check(user, f"{APP_LABEL}.delete_{model_key}")

# ────────── Role helpers ──────────
def is_staff_user(user):
    return bool(user.is_authenticated and (user.is_staff or user.is_superuser))


def is_student_user(user):
    return (
        user.is_authenticated
        and not is_staff_user(user)
        and getattr(user, "category", None) == "STUDENT"
    )


def get_student_engagement(user):
    try:
        return user.engagement_details
    except Exception:
        return None


# ────────── Query helpers (safe) ──────────
def safe_count(model):
    try:
        return model.objects.count()
    except DatabaseError:
        logger.exception("Count failed for %s", model.__name__)
        return None
    except Exception:
        logger.exception("Unexpected count error for %s", model.__name__)
        return None


def safe_queryset(model):
    try:
        qs = model.objects.all()
        # select_related for FK to avoid N+1
        fk_names = [
            f.name for f in model._meta.fields
            if f.is_relation and f.many_to_one
        ]
        if fk_names:
            qs = qs.select_related(*fk_names)
        return qs
    except Exception:
        logger.exception("Query failed for %s", model.__name__)
        return model.objects.none()


def safe_admin_url(model_key, action="changelist", pk=None):
    try:
        if action == "changelist":
            return reverse(f"admin:{APP_LABEL}_{model_key}_changelist")
        if action == "add":
            return reverse(f"admin:{APP_LABEL}_{model_key}_add")
        if action == "change" and pk is not None:
            return reverse(f"admin:{APP_LABEL}_{model_key}_change", args=[pk])
    except NoReverseMatch:
        return None
    except Exception:
        logger.exception("admin URL build failed for %s/%s", model_key, action)
        return None
    return None


# ────────── Field/Table helpers ──────────
def get_concrete_fields(model, exclude=None):
    exclude = set(exclude or [])
    fields = []
    for f in model._meta.fields:
        if f.name in exclude:
            continue
        if not f.concrete:
            continue
        fields.append(f)
    return fields


def format_field_value(obj, field):
    """HTML-safe format of a field value; returns SafeString for links."""
    try:
        name = field.name

        # Choice display
        if getattr(field, "choices", None):
            disp = getattr(obj, f"get_{name}_display", None)
            if disp:
                v = disp()
                return str(v) if v not in (None, "") else "—"

        value = getattr(obj, name, None)

        if value is None or value == "":
            return "—"

        if isinstance(value, bool):
            return "✅ Yes" if value else "❌ No"

        if isinstance(field, (models.FileField, models.ImageField)):
            try:
                return format_html(
                    '<a href="{}" target="_blank" rel="noopener">📎 Open</a>',
                    value.url,
                )
            except (ValueError, AttributeError):
                return "—"

        if isinstance(value, datetime.datetime):
            return value.strftime("%d %b %Y, %I:%M %p")

        if isinstance(value, datetime.date):
            return value.strftime("%d %b %Y")

        if isinstance(value, Decimal):
            return f"{value:.2f}"

        if field.is_relation:
            return str(value)

        s = str(value)
        return (s[:90] + "…") if len(s) > 90 else s
    except Exception:
        logger.exception(
            "Format failed for %s.%s",
            type(obj).__name__,
            getattr(field, "name", "?"),
        )
        return "—"

def build_grouped_tables(model, group_by=None, exclude_fields=None, max_rows=None):
    """
    Returns:
      [{
        "label": ...,
        "count": N,
        "headers": [...],
        "rows": [{"pk": 1, "cells": [...]}, ...],   # ← now dict
        "truncated": bool,
      }, ...]
    """
    from .config import MAX_ROWS_PER_GROUP
    max_rows = max_rows or MAX_ROWS_PER_GROUP
    fields = get_concrete_fields(model, exclude=exclude_fields)
    headers = [
        (f.verbose_name.title() if f.verbose_name else f.name) for f in fields
    ]

    def _row(obj):
        return {
            "pk": obj.pk,
            "cells": [format_field_value(obj, f) for f in fields],
        }

    base_qs = safe_queryset(model)

    # ── No grouping ──
    if not group_by:
        try:
            total = base_qs.count()
            rows = [_row(o) for o in base_qs[:max_rows]]
            return [{
                "label": None,
                "count": total,
                "headers": headers,
                "rows": rows,
                "truncated": total > max_rows,
            }]
        except Exception:
            logger.exception("Build table failed for %s", model.__name__)
            return [{
                "label": None, "count": 0, "headers": headers,
                "rows": [], "truncated": False,
            }]

    # ── Invalid group field → fallback ──
    try:
        gfield = model._meta.get_field(group_by)
    except Exception:
        logger.warning("Invalid group_by '%s' on %s", group_by, model.__name__)
        return build_grouped_tables(model, None, exclude_fields, max_rows)

    groups = []

    # ── Choice field ──
    if getattr(gfield, "choices", None):
        for value, display in gfield.choices:
            try:
                qs = base_qs.filter(**{group_by: value})
                total = qs.count()
                rows = [_row(o) for o in qs[:max_rows]]
                groups.append({
                    "label": display, "count": total,
                    "headers": headers, "rows": rows,
                    "truncated": total > max_rows,
                })
            except Exception:
                logger.exception("Group build failed: %s/%s", model.__name__, value)
        return groups

    # ── FK grouping ──
    if gfield.is_relation and gfield.many_to_one:
        try:
            RelModel = gfield.related_model
            rel_pks = base_qs.values_list(f"{group_by}_id", flat=True).distinct()
            for pk in rel_pks:
                if pk is None:
                    label = "— (None)"
                    qs = base_qs.filter(**{f"{group_by}_id": None})
                else:
                    try:
                        label = str(RelModel.objects.get(pk=pk))
                    except RelModel.DoesNotExist:
                        label = f"Missing #{pk}"
                    qs = base_qs.filter(**{f"{group_by}_id": pk})
                total = qs.count()
                rows = [_row(o) for o in qs[:max_rows]]
                groups.append({
                    "label": label, "count": total,
                    "headers": headers, "rows": rows,
                    "truncated": total > max_rows,
                })
        except Exception:
            logger.exception("FK grouping failed for %s", model.__name__)
        return groups

    # ── Plain distinct ──
    try:
        vals = base_qs.values_list(group_by, flat=True).distinct()
        for val in vals:
            label = str(val) if val not in (None, "") else "— (Empty)"
            qs = base_qs.filter(**{group_by: val})
            total = qs.count()
            rows = [_row(o) for o in qs[:max_rows]]
            groups.append({
                "label": label, "count": total,
                "headers": headers, "rows": rows,
                "truncated": total > max_rows,
            })
    except Exception:
        logger.exception("Plain grouping failed for %s", model.__name__)

    return groups


# ────────── 2FA availability checks ──────────
def user_has_two_factor_2fa(user):
    """
    Kya user ke paas django-two-factor-auth ka CONFIRMED device hai?
    """
    try:
        from django_otp import devices_for_user
        return any(d.confirmed for d in devices_for_user(user))
    except Exception:
        logger.exception("user_has_two_factor_2fa failed for %s", getattr(user, "pk", "?"))
        return False


def user_has_dashboard_totp(user):
    """Kya dashboard ka apna TOTP enabled hai?"""
    try:
        from .models import UserTOTP
        return UserTOTP.objects.filter(user=user, is_enabled=True).exists()
    except Exception:
        logger.exception("user_has_dashboard_totp failed for %s", getattr(user, "pk", "?"))
        return False


def user_has_any_2fa(user):
    """Koi bhi 2FA (dashboard ya two_factor) enabled hai?"""
    return user_has_two_factor_2fa(user) or user_has_dashboard_totp(user)