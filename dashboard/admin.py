from django.contrib import admin

# Register your models here.
from . import models

admin.site.register(models.UserTOTP)


admin.site.register(models.ChatLog)
admin.site.register(models.BotKnowledge)
admin.site.register(models.RestrictedKeyword)
admin.site.register(models.StudentLead)
