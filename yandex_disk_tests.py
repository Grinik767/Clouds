import unittest
from os import getenv
from yandex_disk_api_client import YandexDisk
from system_class import SystemClass


class YandexDiskTests(unittest.TestCase):
    def setUp(self):
        SystemClass.load_env()
        self.cloud = YandexDisk(getenv("DEV_AUTH_TOKEN"))

    def test_auth_ok(self):
        self.cloud.auth(getenv("DEV_AUTH_TOKEN"))

    def test_auth_fail(self):
        self.assertRaises(Exception, self.cloud.auth, getenv("DEV_AUTH_TOKEN") + "ab")
