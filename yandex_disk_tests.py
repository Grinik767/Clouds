import unittest
from os import getenv, path
from yandex_disk_api_client import YandexDisk
from system_class import SystemClass


class YandexDiskTests(unittest.TestCase):
    def setUp(self):
        SystemClass.load_env()
        self.cloud = YandexDisk(getenv("DEV_AUTH_TOKEN"))

    def test_auth_ok(self):
        try:
            self.cloud.auth(getenv("DEV_AUTH_TOKEN"))
        except Exception:
            self.fail("Ошибка авторизации")

    def test_auth_fail(self):
        self.assertRaises(Exception, self.cloud.auth, getenv("DEV_AUTH_TOKEN") + "ab")

    def test_disk_info(self):
        response = self.cloud.get_disk_info()
        self.assertEqual(["login", "name", "total_space", "used_space"], list(response.keys()))
        self.assertEqual("anonymous.wind", response["login"])
        self.assertEqual("anonymous.wind", response["name"])

    def test_configure_ok_remote_local(self):
        try:
            self.cloud.configure("/folder", path.dirname(__file__))
        except Exception:
            self.fail("Ошибка конфигурации")

    def test_configure_fail_remote_not_folder(self):
        self.assertRaises(Exception, self.cloud.configure, "/folder/file.docx", path.dirname(__file__))

    def test_configure_fail_remote_not_exist(self):
        self.assertRaises(Exception, self.cloud.configure, "/folder1", path.dirname(__file__))

    def test_configure_fail_local(self):
        self.assertRaises(Exception, self.cloud.configure, "/folder", path.abspath(__file__))
