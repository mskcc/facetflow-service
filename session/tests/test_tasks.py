from rest_framework.test import APITestCase
from session.models import Session, SessionStatus


class TaskTests(APITestCase):

    def test_get_free_port(self):
        pass
        # free_port = get_free_port("1001-2001")
        # print(free_port)