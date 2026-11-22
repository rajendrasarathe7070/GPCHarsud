from django.apps import AppConfig

class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"
    verbose_name = "Institute Dashboard"
    
class ChatbotConfig(AppConfig):
    def ready(self):
        from .services import faq_cache, refresh_restricted_cache
        import threading
        threading.Thread(target=faq_cache.refresh, daemon=True).start()
        threading.Thread(target=refresh_restricted_cache, daemon=True).start()