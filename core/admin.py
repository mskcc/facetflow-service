from django.contrib import admin
from core.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user__username", "user__first_name", "user__last_name", "access_level")
    search_fields = ("user__username",)
