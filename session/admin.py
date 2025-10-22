from session.models import Session
from django.contrib import admin
from django.contrib import messages
from session.session_manager import start_session, stop_session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "port", "status", "started_at", "stopped_at", "session_url")
    list_filter = ("started_at", "stopped_at")
    search_fields = ("name", "description")
    ordering = ("-started_at",)
    actions = ['start_session_action',  'stop_session_action']

    def start_session_action(self, request, queryset):
        for session in queryset:
            start_session(str(session.id))
            messages.success(request, f'Started session "{session.name}"')
    start_session_action.short_description = "Start selected sessions"

    def stop_session_action(self, request, queryset):
        for session in queryset:
            stop_session(str(session.id))
            messages.success(request, f'Stopped session "{session.name}"')
    stop_session_action.short_description = "Stop selected sessions"
