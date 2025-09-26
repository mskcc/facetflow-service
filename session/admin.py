from session.models import Session
from django.contrib import admin


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "port", "status", "started_at", "stopped_at", "session_url")
    list_filter = ("started_at", "stopped_at")
    search_fields = ("name", "description")
    ordering = ("-started_at",)