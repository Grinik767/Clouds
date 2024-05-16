import unittest
from os import getenv, path
from one_drive_api_client import GoogleDrive


class GoogleDriveTests(unittest.TestCase):
    def setUp(self):
        self.cloud = GoogleDrive("")

    def verifyComplexException(self, exception_type, message, callable, *args):
        with self.assertRaises(exception_type) as cm:
            callable(*args)
        self.assertEqual(message, cm.exception.args[0])

    def test_cloud_info(self):
        response = self.cloud.get_cloud_info()
        self.assertEqual(["login", "name", "total_space", "used_space"], list(response.keys()))
        self.assertEqual("pythontaskowich@gmail.com", response["login"])
        self.assertEqual("Python Taskowich", response["name"])

    def test_get_folder_content_ok(self):
        self.assertDictEqual({'folders': ["marioPipe"], 'files': ['supermario85dxsuper.ttf']},
                             self.cloud.get_folder_content("folder"))

    def test_get_folder_content_fail(self):
        self.verifyComplexException(Exception,
                                    "DiskNotFoundError. Не удалось найти запрошенный ресурс или он не является папкой.",
                                    self.cloud.get_folder_content, "folder1")

    def test_get_folder_content_fail_not_folder(self):
        self.verifyComplexException(Exception,
                                    "DiskNotFoundError. Не удалось найти запрошенный ресурс или он не является папкой.",
                                    self.cloud.get_folder_content, "folder/supermario85dxsuper.ttf")

    def test_upload_file_ok(self):
        self.assertDictEqual({"status": "ok"},
                             self.cloud.upload_file(path.join(path.dirname(__file__), 'for_tests', '1.txt'),
                                                    "folder"))

    def test_upload_file_fail_local(self):
        self.verifyComplexException(Exception,
                                    "NotAFile. Загружаемый ресурс не является файлом",
                                    self.cloud.upload_file, path.join(path.dirname(__file__), 'for_tests'),
                                    "folder/marioPipe/1.txt")

    def test_upload_file_fail_remote(self):
        self.verifyComplexException(Exception,
                                    "DiskPathDoesntExistsError. Указанного пути \"folders123/2.txt\" не существует.",
                                    self.cloud.upload_file, path.join(path.dirname(__file__), 'for_tests', '1.txt'),
                                    "folders123/2.txt")

    def test_download_file_ok(self):
        self.assertDictEqual({"status": "ok"}, self.cloud.download_file("folder/file.docx",
                                                                        path.join(path.dirname(__file__), "file.docx")))

    def test_download_file_fail_remote(self):
        self.verifyComplexException(Exception,
                                    "DiskNotFoundError. Не удалось найти запрошенный ресурс.",
                                    self.cloud.download_file, "folder/file123.docx",
                                    path.join(path.dirname(__file__), "file.docx"))

    def test_download_file_fail_remote_not_file(self):
        self.verifyComplexException(Exception,
                                    "NotAFile. Запрошенный ресурс не является файлом",
                                    self.cloud.download_file, "folder", path.join(path.dirname(__file__), "file.docx"))

    def test_download_file_fail_local(self):
        self.verifyComplexException(Exception,
                                    f"FileNotFoundError. Неверный путь: {path.join(path.dirname(__file__), 'files123', 'file.docx')}",
                                    self.cloud.download_file, "folder/file.docx",
                                    path.join(path.dirname(__file__), 'files123', 'file.docx'))

    def test_create_folder_ok(self):
        self.assertDictEqual({"status": "ok"}, self.cloud.create_folder("folder/fold"))

