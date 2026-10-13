from django import template
from django.apps import apps
from django.db import OperationalError, connection

from django.contrib.admin.models import LogEntry

register = template.Library()

@register.simple_tag
def get_model_rows(app_label, model_name):
    try:
        model = apps.get_model(app_label, model_name)
        
        # Safe check: Kya sach me yeh table database me exist karti hai?
        table_name = model._meta.db_table
        if table_name not in connection.introspection.table_names():
            return [] # Table nahi hai to khali list bhej do, error mat do
            
        return model.objects.all()
    except (LookupError, OperationalError):
        return []


@register.simple_tag
def get_history(limit=20):
    return LogEntry.objects.select_related("user", "content_type").order_by("-action_time")[:limit]