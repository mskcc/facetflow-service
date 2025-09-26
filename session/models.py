import uuid
from enum import IntEnum
from django.db import models
from django.contrib.auth.models import User


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(auto_now=True)


class SessionStatus(IntEnum):
    CREATED = 0
    STARTING = 1
    RUNNING = 2
    STOPPED = 3


class Session(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    status = models.IntegerField(
        choices=[(status.value, status.name) for status in SessionStatus], default=SessionStatus.CREATED, db_index=True
    )
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, db_index=True)
    container = models.CharField(max_length=100, default=None, blank=True, null=True)
    work_directory = models.CharField(max_length=1000, default=None, blank=True, null=True)
    port = models.CharField(max_length=4, blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    stopped_at = models.DateTimeField(blank=True, null=True)
    session_url = models.URLField(max_length=1000, blank=True, null=True)
