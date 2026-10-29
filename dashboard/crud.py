import logging
from django import forms
logger = logging.getLogger(__name__)

AUTO_EXCLUDE = {"id", "pk", "password", "last_login", "date_joined", "is_superuser", "user_permissions"}

def build_model_form(model, config_excludes=None):
    try:
        exclude = set(AUTO_EXCLUDE)
        if config_excludes: exclude.update(config_excludes)
        for f in model._meta.fields:
            if not getattr(f, "editable", True) or getattr(f, "auto_now", False) or getattr(f, "auto_now_add", False):
                exclude.add(f.name)
        return forms.modelform_factory(model, exclude=list(exclude))
    except Exception:
        logger.exception("build_model_form failed")
        return None

def style_form_fields(form):
    try:
        for field in form.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"
    except Exception:
        logger.exception("style_form_fields failed")