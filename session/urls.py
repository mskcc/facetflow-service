from django.urls import path

from .models import SessionStatus
from .views import StartSessionView, StopSessionView, ResumeSessionView, SessionView

urlpatterns = [
    path("start/", StartSessionView.as_view(), name="start-session"),
    path("stop/", StopSessionView.as_view(), name="stop-session"),
    path("resume/", ResumeSessionView.as_view(), name="resume-session"),
    path("list/", SessionView.as_view(), name="sessions-list"),
]