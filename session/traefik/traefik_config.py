import yaml
import json
from copy import deepcopy
from django.conf import settings

ROUTER_SESSION = {
    "entryPoints": ["web"],
    "middlewares": ["strip-{short_id}", "set-cookie-{short_id}"],
    "rule": 'PathPrefix("/{session_id}")',
    "service": "s-{short_id}"
}

ROUTER_SESSION_SESSIONS = {
    "entryPoints": ["web"],
    "rule": 'PathPrefix("/session") && HeaderRegexp("Cookie", "ext_uuid_{short_id}=1")',
    "service": "s-{short_id}",
    "priority": 900
}

ROUTER_SESSION_SHARED = {
    "entryPoints": ["web"],
    "rule": 'PathPrefix("/shared") && HeaderRegexp("Cookie", "ext_uuid_{short_id}=1")',
    "service": "s-{short_id}",
    "priority": 900
}

ROUTER_SESSION_SOCK = {
    "entryPoints": ["web"],
    "rule": 'PathPrefix("/__sockjs__/") && HeaderRegexp("Cookie", "ext_uuid_{short_id}=1")',
    "service": "s-{short_id}",
    "priority": 900
}

ROUTER_SESSION_STATIC = {
    "entryPoints": ["web"],
    "rule": 'PathPrefix("/static") && HeaderRegexp("Cookie", "ext_uuid_{short_id}=1")',
    "service": "s-{short_id}",
    "priority": 900
}

ROUTER_SESSION_ASSETS = {
    "entryPoints": ["web"],
    "rule": 'PathRegexp(".(css|js|png|jpg|svg|woff2?)$") && HeaderRegexp("Cookie", "ext_uuid_{short_id}=1")',
    "service": "s-{short_id}",
    "priority": 800
}

# ROUTER_SESSION_DATAOBJ = {
#     "entryPoints": ["web"],
#     "rule": "PathPrefix(`/dataobj`)",
#     "service": "s-{short_id}"
# }

MIDDLEWARE_STRIP_SESSION = {"stripPrefix": {"prefixes": ["/{session_id}"]}}
MIDDLEWARE_SET_COOKIE = {
    "headers": {
        "customResponseHeaders": {
            "Set-Cookie": "ext_uuid_{short_id}=1; Path=/; HttpOnly; SameSite=Lax"}
    }
}

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
        short_id = session_id.split('-')[0]

        # Update router
        router_session = deepcopy(ROUTER_SESSION)
        router_session["rule"] = router_session["rule"].format(session_id=session_id)
        router_session["middlewares"][0] = router_session["middlewares"][0].format(short_id=short_id)
        router_session["middlewares"][1] = router_session["middlewares"][1].format(short_id=short_id)
        router_session["service"] = router_session["service"].format(short_id=short_id)
        self.data["http"]["routers"][f"r-{short_id}-html"] = router_session

        router_session_sessions = deepcopy(ROUTER_SESSION_SESSIONS)
        router_session_sessions["rule"] = router_session_sessions["rule"].format(short_id=short_id)
        router_session_sessions["service"] = router_session_sessions["service"].format(short_id=short_id)
        self.data["http"]["routers"][f"r-{short_id}-sessions"] = router_session_sessions

        router_session_shared = deepcopy(ROUTER_SESSION_SHARED)
        router_session_shared["rule"] = router_session_shared["rule"].format(short_id=short_id)
        router_session_shared["service"] = router_session_shared["service"].format(short_id=short_id)
        self.data["http"]["routers"][f"r-{short_id}-shared"] = router_session_shared

        router_session_sock = deepcopy(ROUTER_SESSION_SOCK)
        router_session_sock["rule"] = router_session_sock["rule"].format(short_id=short_id)
        router_session_sock["service"] = router_session_sock["service"].format(short_id=short_id)
        self.data["http"]["routers"][f"r-{short_id}-sock"] = router_session_sock

        router_session_static = deepcopy(ROUTER_SESSION_STATIC)
        router_session_static["rule"] = router_session_static["rule"].format(short_id=short_id)
        router_session_static["service"] = router_session_static["service"].format(short_id=short_id)
        self.data["http"]["routers"][f"r-{short_id}-static"] = router_session_static

        router_session_assets = deepcopy(ROUTER_SESSION_ASSETS)
        router_session_assets["rule"] = router_session_assets["rule"].format(short_id=short_id)
        router_session_assets["service"] = router_session_assets["service"].format(short_id=short_id)
        self.data["http"]["routers"][f"r-{short_id}-assets"] = router_session_assets

        # Update middleware
        middleware_strip_session = deepcopy(MIDDLEWARE_STRIP_SESSION)
        middleware_strip_session["stripPrefix"]["prefixes"][0] = middleware_strip_session["stripPrefix"]["prefixes"][
            0].format(session_id=session_id)
        self.data["http"]["middlewares"][f"strip-{short_id}"] = middleware_strip_session

        middleware_set_cookie = deepcopy(MIDDLEWARE_SET_COOKIE)
        middleware_set_cookie["headers"]["customResponseHeaders"]["Set-Cookie"] = \
        middleware_set_cookie["headers"]["customResponseHeaders"]["Set-Cookie"].format(short_id=short_id)
        self.data["http"]["middlewares"][f"set-cookie-{short_id}"] = middleware_set_cookie

        # Update services
        service_session = deepcopy(SERVICES_SESSION)
        service_session["loadBalancer"]["servers"][0]["url"] = service_session["loadBalancer"]["servers"][0]["url"].format(port=port)
        self.data["http"]["services"][f"s-{short_id}"] = service_session

    def stop_session(self, session_id):
        short_id = session_id.split('-')[0]

        self.data["http"]["routers"].pop(f"r-{short_id}-html", None)
        self.data["http"]["routers"].pop(f"r-{short_id}-sessions", None)
        self.data["http"]["routers"].pop(f"r-{short_id}-shared", None)
        self.data["http"]["routers"].pop(f"r-{short_id}-sock", None)
        self.data["http"]["routers"].pop(f"r-{short_id}-static", None)
        self.data["http"]["routers"].pop(f"r-{short_id}-assets", None)
        self.data["http"]["middlewares"].pop(f"set-cookie-{short_id}", None)
        self.data["http"]["middlewares"].pop(f"strip-{short_id}", None)
        self.data["http"]["services"].pop(f"s-{short_id}", None)

    def __str__(self):
        return json.dumps(self.data, indent=4)