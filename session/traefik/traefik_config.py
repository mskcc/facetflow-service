import yaml
from copy import deepcopy
from django.conf import settings

ROUTER_SESSION = {"entryPoints": ["web"], "middlewares": ["strip-{session_id}"], "rule": "PathPrefix(`/{session_id}`)", "service": "{session_id}"}
ROUTER_SESSION_ASSETS = {"entryPoints": ["web"], "rule": "PathRegexp(`\\.(css|js|png|jpg|woff2?)$`)", 'service': "{session_id}"}
ROUTER_SESSION_DATAOBJ = {"entryPoints": ["web"], "rule": "PathPrefix(`/dataobj`)", "service": "{session_id}"}
ROUTER_SESSION_STATIC = {"entryPoints": ["web"], "rule": "PathPrefix(`/static`)", "service": "{session_id}"}
ROUTER_SESSION_SESSIONS = {"entryPoints": ["web"], "rule": "PathPrefix(`/session`)", "service": "{session_id}"}

MIDDLEWARE_STRIP_SESSION = {'stripPrefix': {'prefixes': ['/{session_id}']}}

SERVICES_SESSION = {'loadBalancer': {'servers': [{'url': 'http://host.docker.internal:{port}'}]}}


class TraefikConfig(object):

    def __init__(self, data):
        self.data = data

    @classmethod
    def load(cls, path=settings.TRAEFIK_CONFIG):
        with open(path, "r") as f:
           data = yaml.safe_load(f)
        return cls(data)

    def to_yaml(self):
        return yaml.dump(self.data)

    def dump(self, path=settings.TRAEFIK_CONFIG):
        with open(path, "w") as f:
            yaml.dump(self.data, f)

    def start_session(self, session_id, port):
        # Update router
        router_session = deepcopy(ROUTER_SESSION)
        router_session["middlewares"][0] = router_session["middlewares"][0].format(session_id=session_id)
        router_session["rule"] = router_session["rule"].format(session_id=session_id)
        router_session["service"] = router_session["service"].format(session_id=session_id)
        self.data["http"]["routers"][session_id] = router_session

        router_session_assets = deepcopy(ROUTER_SESSION_ASSETS)
        router_session_assets["service"] = router_session_assets["service"].format(session_id=session_id)
        self.data["http"]["routers"][f"{session_id}-assets"] = router_session_assets

        router_session_dataobj = deepcopy(ROUTER_SESSION_DATAOBJ)
        router_session_dataobj["service"] = router_session_dataobj["service"].format(session_id=session_id)
        self.data["http"]["routers"][f"{session_id}-dataobj"] = router_session_assets

        router_session_static = deepcopy(ROUTER_SESSION_STATIC)
        router_session_static["service"] = router_session_static["service"].format(session_id=session_id)
        self.data["http"]["routers"][f"{session_id}-static"] = router_session_static

        router_session_sessions = deepcopy(ROUTER_SESSION_SESSIONS)
        router_session_sessions["service"] = router_session_sessions["service"].format(session_id=session_id)
        self.data["http"]["routers"][f"{session_id}-sessions"] = router_session_sessions
        # Update middleware
        middleware_strip_session = deepcopy(MIDDLEWARE_STRIP_SESSION)
        middleware_strip_session["stripPrefix"]["prefixes"][0] = middleware_strip_session["stripPrefix"]["prefixes"][
            0].format(session_id=session_id)
        self.data["http"]["middlewares"][f"strip-{session_id}"] = middleware_strip_session
        # Update services
        service_session = deepcopy(SERVICES_SESSION)
        service_session["loadBalancer"]["servers"][0]["url"] = service_session["loadBalancer"]["servers"][0]["url"].format(port=port)
        self.data["http"]["services"][session_id] = service_session

    def stop_session(self, session_id):
        self.data["http"]["routers"].pop(session_id, None)
        self.data["http"]["routers"].pop(f"{session_id}-assets", None)
        self.data["http"]["routers"].pop(f"{session_id}-dataobj", None)
        self.data["http"]["routers"].pop(f"{session_id}-static", None)
        self.data["http"]["routers"].pop(f"{session_id}-sessions", None)
        self.data["http"]["middlewares"].pop(f"strip-{session_id}", None)
        self.data["http"]["services"].pop(session_id, None)
