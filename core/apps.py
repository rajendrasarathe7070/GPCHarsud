from django.apps import AppConfig


 

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'   # apna app name

    def ready(self):
        import cacheops
        from django.db.models.query import QuerySet
        from cacheops.conf import model_profile

        _orig_filter = QuerySet.filter
        _orig_all = QuerySet.all
        _orig_get = QuerySet.get

        def _should_cache(qs):
            """Sirf un models ke queries cache karo jo CACHEOPS me listed hain."""
            try:
                profile = model_profile(qs.model)
                return profile is not None and bool(profile.cache_ops)
            except Exception:
                return False

        def cached_filter(self, *args, **kwargs):
            qs = _orig_filter(self, *args, **kwargs)
            return qs.cache() if _should_cache(qs) else qs

        def cached_all(self):
            qs = _orig_all(self)
            return qs.cache() if _should_cache(qs) else qs

        QuerySet.filter = cached_filter
        QuerySet.all = cached_all