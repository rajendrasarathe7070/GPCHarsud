from django.db import models

# Create your models here.
import logging

from django.conf import settings
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class UserTOTP(models.Model):
    """
    Har user ka TOTP secret + settings.
    By default is_enabled=False → login par "setup or skip" poocha jaata hai.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="totp",
    )
    secret = models.CharField(max_length=64)
    is_enabled = models.BooleanField(default=False)

    # Backup codes (hashed nahi, plain — chaho to hash kar sakte ho)
    backup_codes = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    # Brute-force protection
    failed_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "User TOTP"
        verbose_name_plural = "User TOTP Records"

    def __str__(self):
        status = "✅" if self.is_enabled else "❌"
        return f"{status} {self.user}"

    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def register_success(self):
        self.last_used_at = timezone.now()
        self.failed_attempts = 0
        self.locked_until = None
        self.save(update_fields=["last_used_at", "failed_attempts", "locked_until"])

    def register_failure(self, max_attempts=5, lock_minutes=15):
        from datetime import timedelta
        self.failed_attempts = (self.failed_attempts or 0) + 1
        if self.failed_attempts >= max_attempts:
            self.locked_until = timezone.now() + timedelta(minutes=lock_minutes)
        self.save(update_fields=["failed_attempts", "locked_until"])