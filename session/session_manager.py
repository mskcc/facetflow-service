import os
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from django.conf import settings
from session.models import Session, SessionStatus
from session.facets.facets_app import FacetsApp
from session.traefik.traefik_config import TraefikConfig


logger = logging.getLogger(__name__)


def get_free_port(port_range=settings.PORT_RANGE):
    """
    get free port from port_range
    TODO: Implement lock so two sessions can have the same port
    """
    ports = Session.objects.filter(status=SessionStatus.RUNNING).values_list("port", flat=True)
    occupied_port_set = set(int(p) for p in ports)
    start_str, end_str = port_range.split('-')
    start_port = int(start_str.strip())
    end_port = int(end_str.strip())
    if start_port < 1 or end_port > 65535:
        raise ValueError("Ports must be between 1 and 65535")
    if start_port > end_port:
        raise ValueError("Start port must be less than or equal to end port")
    for port in range(start_port, end_port + 1):
        if port not in occupied_port_set:
            return port
    return None


def start_session(session_id):
    """
    Start a new session
    TODO: Move this to tasks.py
    """
    session = Session.objects.get(id=session_id)
    work_directory_path = os.path.join(settings.BASE_WORK_DIR, session.owner.username, str(session_id))
    if not session.work_directory:
        session.work_directory = work_directory_path
        Path(work_directory_path).mkdir(parents=True, exist_ok=True)
    session.work_directory = work_directory_path
    session.save(update_fields=["work_directory"])
    try:
        port = get_free_port()
        session.port = port
        facets = FacetsApp(session_id, port, work_directory_path, session.owner.username)
        container = facets.start()
    except Exception as e:
        logger.error(e)
        raise
    session.container = container.id
    session.save(update_fields=["port","container"])
    # config = TraefikConfig.load()
    # config.start_session(session_id, port)
    # config.dump()
    start_time = datetime.now()
    session.started_at = start_time
    session.status = SessionStatus.RUNNING

    session.session_url = f"{settings.FACETS_TRAEFIK_URL}:{str(port)}"
    session.save(update_fields=["started_at", "status", "session_url"])

def stop_session(session_id):
    """
    Stop a session
    TODO: Move this to tasks.py
    """
    session = Session.objects.get(id=session_id)
    try:
        facets = FacetsApp(session_id, session.port, session.work_directory, session.owner.username)
        facets.stop()
        session.port = None
        session.save(update_fields=["port"])
    except Exception as e:
        logger.error(e)
        raise
    config = TraefikConfig.load()
    config.stop_session(session_id)
    config.dump()
    stop_time = datetime.now()
    session.stopped_at = stop_time
    session.status = SessionStatus.STOPPED
    session.session_url = None
    session.save()