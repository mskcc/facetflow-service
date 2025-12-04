import logging
import docker
from django.conf import settings
from core.models import AccessLevel
from django.contrib.auth import get_user_model


User = get_user_model()

"""
docker run -v $HOME:/root -v /Users/:/Users/ --workdir $2 -p $1:3838 --name $3 --rm  price0416/fp_docker:latest /bin/bash
"""

class FacetsApp(object):

    logger = logging.getLogger(__name__)

    def __init__(self, session_id, port, work_dir, username, facets_image=settings.FACETS_IMAGE,
                 container_port=settings.FACETS_CONTAINER_PORT, base_work_dir=settings.BASE_WORK_DIR):
        self.session_id = session_id
        self.port = port
        self.work_dir = work_dir
        self.facets_image = facets_image
        self.container_port = container_port
        self.base_work_dir = base_work_dir
        self.username = username

    def start(self):
        client = docker.from_env()
        user = User.objects.get(username=self.username)
        ports = {
            self.container_port: self.port
        }
        volumes = {
            self.base_work_dir: {
                "bind": self.base_work_dir,
                "mode": "rw"
            }
        }

        environment = [
            'FP_MODE=vm',
            f'FP_USER_ID={self.username}',
            f'FP_USER_BASE_WORKDIR={self.base_work_dir}',
            f'FP_USER_WORKDIR={self.work_dir}',
            f'FP_ACCESS_LEVEL={AccessLevel(user.userprofile.access_level).name}',
            f'FP_IRIS_RSCRIPT={settings.FACETS_IRIS_RSCRIPT}',
            f'FP_IRIS_WRAPPER={settings.FACETS_IRIS_WRAPPER}',
            f'FP_IRIS_RLIBS={settings.FACETS_IRIS_RLIBS}',
            f'FP_IRIS_REFIT_QUEUE={settings.FACETS_IRIS_REFIT_QUEUE}'
        ]
        mount_points = settings.MOUNT_POINTS.split(",")
        for mount_point in mount_points:
            volumes[mount_point] = {
                "bind": mount_point,
                "mode": "rw"
            }
        container = client.containers.run(
            image=settings.FACETS_IMAGE,
            name=self.session_id,
            ports=ports,
            volumes=volumes,
            environment=environment,
            working_dir=self.work_dir,
            user=f"{settings.FACETS_CONTAINER_USER}:{settings.FACETS_CONTAINER_GROUP}",
            group_add=settings.FACETS_CONTAINER_ADDITIONAL_GROUPS,
            detach=True
        )
        print(f"Container started: {container.id}")
        return container

    def stop(self):
        client = docker.from_env()
        container = client.containers.get(self.session_id)
        container.stop()
        container.remove()
