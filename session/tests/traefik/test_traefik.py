import os
import uuid
import datetime
from pathlib import Path
current_file_path = os.path.abspath(__file__)
from rest_framework import status
from rest_framework.test import APITestCase
from session.traefik.traefik_config import TraefikConfig


class TraefikTests(APITestCase):

    def setUp(self):
        pass

    def test_add_session(self):
        current_file_path = os.path.abspath(__file__)
        config_path = os.path.join(Path(current_file_path).parent, "test.yml")
        config = TraefikConfig.load(path=config_path)
        test_id = "60d9b1ba-ea96-44cb-afc9-117d407383a8"
        config.start_session(test_id, "1000")
        print(config)
        config.stop_session(test_id)
        print(config)