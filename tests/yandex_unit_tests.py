import pytest
import httpx
from pytest_httpx import HTTPXMock
from yandex_disk_api_client import YandexDisk


@pytest.fixture
def cloud(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"https://cloud-api.yandex.net/v1/disk/",
        method="GET",
        match_headers={"Authorization": "1234"},
        status_code=httpx.codes.OK
    )
    return YandexDisk(auth_token="1234")


def test_auth_fail(cloud: YandexDisk, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"https://cloud-api.yandex.net/v1/disk/",
        method="GET",
        status_code=httpx.codes.UNAUTHORIZED
    )
    with pytest.raises(Exception) as e_info:
        cloud.auth("1234")
    assert e_info.value.args[0] == 'AuthError. Ошибка авторизации в Яндекс.Диске. Проверьте/обновите данные'


def test_get_cloud_info(cloud: YandexDisk, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{cloud.url}?fields=user.login%2Cuser.display_name%2Ctotal_space%2Cused_space",
        method="GET",
        json={
            "user": {
                "login": "test_user",
                "display_name": "Test User"
            },
            "total_space": 1024 * 2 ** 20,
            "used_space": 512 * 2 ** 20
        },
        match_headers={"Authorization": "1234"},
        status_code=httpx.codes.OK
    )
    cloud_info = cloud.get_cloud_info()
    assert cloud_info["login"] == "test_user" and cloud_info["name"] == "Test User" and cloud_info[
        "total_space"] == 1024 and cloud_info["used_space"] == 512


def test_get_folder_content_ok(cloud: YandexDisk, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{cloud.url}resources?path=%2F&fields=type%2C_embedded.items.name%2C_embedded.items.type",
        method="GET",
        json={
            "type": "dir",
            "_embedded": {
                "items": [
                    {"name": "folder1", "type": "dir"},
                    {"name": "file1.txt", "type": "file"}
                ]
            }
        },
        match_headers={"Authorization": "1234"},
        status_code=httpx.codes.OK
    )
    folder_content = cloud.get_folder_content("/")
    assert ["folder1"] == folder_content["folders"] and ["file1.txt"] == folder_content["files"]


def test_get_folder_content_fail_remote_no_path(cloud: YandexDisk, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{cloud.url}resources?path=%2Fabracad&fields=type%2C_embedded.items.name%2C_embedded.items.type",
        method="GET",
        json={"error": "DiskNotFoundError", "message": "Не удалось найти запрошенный ресурс."},
        match_headers={"Authorization": "1234"},
        status_code=httpx.codes.NOT_FOUND
    )
    with pytest.raises(Exception) as e_info:
        cloud.get_folder_content("/abracad")
    assert e_info.value.args[0] == 'DiskNotFoundError. Не удалось найти запрошенный ресурс.'


def test_get_folder_content_fail_remote_not_folder(cloud: YandexDisk, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{cloud.url}resources?path=folder%2Ffile.docx&fields=type%2C_embedded.items.name%2C_embedded.items.type",
        method="GET",
        json={
            "type": "file",
        },
        match_headers={"Authorization": "1234"},
        status_code=httpx.codes.OK
    )
    with pytest.raises(Exception) as e_info:
        cloud.get_folder_content("folder/file.docx")
    assert e_info.value.args[0] == 'NotAFolder. Запрошенный ресурс не является папкой'


def test_download_file_ok(cloud: YandexDisk, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url=f"{cloud.url}resources/download?path=%2Fpath%2Fto%2Ffile.txt&fields=href",
        method="GET",
        match_headers={"Authorization": "1234"},
        json={"href": "https://download.example.com/file.txt"}
    )
    httpx_mock.add_response(
        url=f"{cloud.url}resources?path=%2Fpath%2Fto%2Ffile.txt&fields=type%2C_embedded.items.name%2C_embedded.items.type",
        method="GET",
        match_headers={"Authorization": "1234"},
        json={"type": "file"}
    )
    httpx_mock.add_response(
        url="https://download.example.com/file.txt",
        content=b"Hello, World!",
        status_code=httpx.codes.OK
    )
    local_path = tmp_path / "file.txt"
    result = cloud.download_file("/path/to/file.txt", str(local_path))
    assert result["status"] == "ok"
    assert local_path.read_bytes() == b"Hello, World!"
