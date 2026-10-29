from django.conf import settings
from django.db import models
from django.utils import timezone

class UserTOTP(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="totp")
    secret = models.CharField(max_length=64)
    is_enabled = models.BooleanField(default=False)
    backup_codes = models.JSONField(default=list, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    failed_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User TOTP"

    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def register_success(self):
        self.last_used_at = timezone.now()
        self.failed_attempts = 0
        self.locked_until = None
        self.save(update_fields=["last_used_at", "failed_attempts", "locked_until"])

    def register_failure(self, max_attempts=5, lock_minutes=15):
        from datetime import timedelta
        self.failed_attempts += 1
        if self.failed_attempts >= max_attempts:
            self.locked_until = timezone.now() + timedelta(minutes=lock_minutes)
        self.save(update_fields=["failed_attempts", "locked_until"])