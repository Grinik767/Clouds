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

    def test_get_folder_content_ok(self):
        self.assertDictEqual({'folders': ["folder1"], 'files': ['file.docx']}, self.cloud.get_folder_content("folder"))

    def test_get_folder_content_fail(self):
        self.assertDictEqual({'error': 'DiskNotFoundError', 'message': 'Не удалось найти запрошенный ресурс.'},
                             self.cloud.get_folder_content("folder1"))

    def test_get_folder_content_fail_not_folder(self):
        self.assertDictEqual({'error': 'NotAFolder', 'message': 'Запрошенный ресурс не является папкой'},
                             self.cloud.get_folder_content("folder/file.docx"))

    def test_create_folder_ok(self):
        self.assertDictEqual({"status": "ok"}, self.cloud.create_folder("folder/fold"))
        self.cloud.delete_folder("folder/fold")

    def test_create_folder_fail(self):
        self.assertEqual("DiskPathPointsToExistentDirectoryError", self.cloud.create_folder("folder")["error"])

    def test_download_file_ok(self):
        self.assertDictEqual({"status": "ok"}, self.cloud.download_file("folder/file.docx", "file.docx"))

    def test_download_file_fail_remote(self):
        self.assertDictEqual({"message": "Не удалось найти запрошенный ресурс.", "error": "DiskNotFoundError"},
                             self.cloud.download_file("folder/file123.docx", "file.docx"))

    def test_download_file_fail_remote_not_file(self):
        self.assertDictEqual({"error": "NotAFile", "message": "Запрошенный ресурс не является файлом"},
                             self.cloud.download_file("folder", "file.docx"))

    def test_download_file_fail_local(self):
        self.assertEqual("FileNotFoundError",
                         self.cloud.download_file("folder/file.docx", "files123/file.docx")["error"])
