import logging

from django import forms

logger = logging.getLogger(__name__)

AUTO_EXCLUDE_FIELDS = {"id", "pk"}

CUSTOMUSER_HARD_EXCLUDE = {
    "password", "last_login", "date_joined",
    "is_superuser", "user_permissions",
    "groups",  # dashboard me group change nahi karne dena (admin pe rakho)
}


def get_crud_exclude_fields(model, config_excludes=None):
    exclude = set(AUTO_EXCLUDE_FIELDS)
    if config_excludes:
        exclude.update(config_excludes)

    if model._meta.model_name == "customuser":
        exclude.update(CUSTOMUSER_HARD_EXCLUDE)

    for f in model._meta.fields:
        if not getattr(f, "editable", True):
            exclude.add(f.name)
        if getattr(f, "auto_created", False):
            exclude.add(f.name)
        if getattr(f, "auto_now_add", False) or getattr(f, "auto_now", False):
            exclude.add(f.name)

    return list(exclude)


def build_model_form(model, config_excludes=None):
    """Dynamically build ModelForm for the given model."""
    exclude = get_crud_exclude_fields(model, config_excludes)
    try:
        FormClass = forms.modelform_factory(model, exclude=exclude)
        return FormClass
    except Exception:
        logger.exception("modelform_factory failed for %s", model.__name__)
        return None


def style_form_fields(form):
    """Add Bootstrap classes to widget inputs."""
    try:
        for name, field in form.fields.items():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault("class", "form-check-input")
            elif isinstance(w, (forms.Select, forms.SelectMultiple)):
                w.attrs.setdefault("class", "form-select")
            elif isinstance(w, (forms.ClearableFileInput, forms.FileInput)):
                w.attrs.setdefault("class", "form-control")
            else:
                w.attrs.setdefault("class", "form-control")
    except Exception:
        logger.exception("style_form_fields failed")


def form_has_file_fields(form):
    try:
        return any(
            isinstance(f, (forms.FileField, forms.ImageField))
            for f in form.fields.values()
        )
    except Exception:
        return False