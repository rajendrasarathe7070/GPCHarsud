from django.apps import AppConfig

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Cacheops और Redis का पुराना सारा लॉजिक यहाँ से हटा दिया गया है
        pass
