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
        
        
    from django.db import models

class BotKnowledge(models.Model):
    question = models.CharField(max_length=500, unique=True)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question


class StudentLead(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    course = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.course}"


# 🆕 हर सवाल-जवाब का log (dashboard stats के लिए)
class ChatLog(models.Model):
    SOURCE_CHOICES = [
        ("fast_db", "Fast DB"),
        ("gemini", "Gemini AI"),
        ("restricted", "Restricted"),
        ("error", "Error"),
    ]
    session_id = models.CharField(max_length=64, blank=True, db_index=True)
    question = models.TextField()
    answer = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, db_index=True)
    success = models.BooleanField(default=True, db_index=True)
    response_ms = models.IntegerField(default=0)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]


# 🆕 Jail/Restrictions के लिए banned keywords
class RestrictedKeyword(models.Model):
    keyword = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, blank=True, default="general")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.keyword} ({self.category})"