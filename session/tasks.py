import os
import dramatiq
from pathlib import Path
from django.conf import settings
from session.facets.facets_app import FacetsApp
from session.models import Session, SessionStatus
from session.traefik.traefik_config import TraefikConfig


@dramatiq.actor
def start_session(session_id):
    pass


def resume_session(session_id):
    pass




