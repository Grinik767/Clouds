from unittest.mock import patch

import pytest
import httpx
from pytest_httpx import HTTPXMock
from dropbox_api_client import Dropbox


@pytest.fixture
def cloud(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"https://api.dropboxapi.com/2/users/get_current_account",
        method="POST"
    )
    return Dropbox(auth_token="1234")


def test_auth_fail(cloud: Dropbox, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{cloud.url}users/get_current_account",
        method="POST",
        status_code=httpx.codes.UNAUTHORIZED,
    )
    with pytest.raises(Exception) as e_info:
        cloud.auth("1234")
    assert e_info.value.args[0] == 'AuthError. Ошибка авторизации в Dropbox. Проверьте/обновите данные'


def test_get_cloud_info(cloud: Dropbox, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{cloud.url}users/get_space_usage",
        method="POST",
        json={
            "used": 512 * 2 ** 20
        }
    )
    httpx_mock.add_response(
        url=f"{cloud.url}users/get_current_account",
        method="POST",
        json={
            "name": {
                "display_name": "Test User"
            },
            "email": "test_user@example.com"
        }
    )
    cloud_info = cloud.get_cloud_info()
    assert cloud_info["name"] == "Test User" and cloud_info["email"] == "test_user@example.com" and cloud_info[
        "used_space"]


def test_get_folder_content_ok(cloud: Dropbox, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/get_metadata",
        method="POST",
        json={
            ".tag": "folder"
        }
    )
    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/list_folder",
        method="POST",
        json={
            "entries": [
                {"name": "folder1", ".tag": "folder"},
                {"name": "file1.txt", ".tag": "file"}
            ],
            "cursor": "mock_cursor",
            "has_more": False
        }
    )
    folder_content = cloud.get_folder_content("")
    assert ["folder1"] == folder_content["folders"] and ["file1.txt"] == folder_content["files"]


def test_get_folder_content_fail_remote(cloud: Dropbox, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/get_metadata",
        method="POST",
        json={
            "error_summary": "path/not_found/."
        },
        status_code=httpx.codes.NOT_FOUND
    )

    with pytest.raises(Exception) as e_info:
        cloud.get_folder_content("/acdcdcd")
    assert e_info.value.args[0] == 'NotFoundError. Не удалось найти запрошенный ресурс.'


def test_get_folder_content_fail_remote_not_folder(cloud: Dropbox, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/get_metadata",
        method="POST",
        json={
            ".tag": ".txt."
        }
    )
    with pytest.raises(Exception) as e_info:
        cloud.get_folder_content("folder/file.docx")
    assert e_info.value.args[0] == 'NotAFolderError. Запрошенный ресурс не является папкой'


def test_download_file_ok(cloud: Dropbox, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url="https://content.dropboxapi.com/2/files/download",
        method="POST",
        content=b"Hello, World!",
    )
    local_path = tmp_path / "file.txt"
    result = cloud.download_file("/path/to/file.txt", str(local_path))
    assert result["status"] == "ok" and local_path.read_bytes() == b"Hello, World!"


def test_download_file_fail_remote(cloud: Dropbox, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url="https://content.dropboxapi.com/2/files/download",
        method="POST",
        json={"error_summary": "path/not_found/."},
        status_code=httpx.codes.NOT_FOUND
    )
    local_path = tmp_path / "file.txt"
    with pytest.raises(Exception) as e_info:
        cloud.download_file("/path/to/file123.docx", str(local_path))
    assert e_info.value.args[0] == 'NotFoundError. Не удалось найти запрошенный ресурс.'


def test_download_file_fail_local(cloud: Dropbox, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url="https://content.dropboxapi.com/2/files/download",
        method="POST",
        content=b"Hello, World!"
    )
    local_path = tmp_path / "abracad" / "file.txt"
    with pytest.raises(Exception) as e_info:
        cloud.download_file("/path/to/file.txt", str(local_path))
    assert e_info.value.args[0] == f'FileNotFoundError. Неверный путь: {str(local_path)}'


def test_upload_file_ok(cloud: Dropbox, httpx_mock: HTTPXMock, tmp_path):
    local_path = tmp_path / "file.txt"
    local_path.write_bytes(b"Hello, World!")
    httpx_mock.add_response(
        url="https://content.dropboxapi.com/2/files/upload",
        method="POST",
        headers={
            "Dropbox-API-Arg": '{"path":"/path/to/file.txt","mode":"overwrite","autorename":true,"mute":false,"strict_conflict":false}'},
        status_code=httpx.codes.OK
    )
    result = cloud.upload_file(str(local_path), "/path/to/file.txt")
    assert result["status"] == "ok"


def test_upload_file_fail_local(cloud: Dropbox, tmpdir):
    folder_path = tmpdir.mkdir("test_folder")
    with pytest.raises(Exception) as e_info:
        cloud.upload_file(str(folder_path), "/path/to/file.txt")
    assert e_info.value.args[0] == 'NotAFileError. Загружаемый ресурс не является файлом'


def test_upload_file_fail_local(cloud, tmpdir):
    non_existent_file = tmpdir.join("non_existent_file.txt")

    with pytest.raises(Exception) as e_info:
        cloud.upload_file(str(non_existent_file), "/path/to/file.txt")

    assert e_info.value.args[0] == 'NotAFileError. Загружаемый ресурс не является файлом'


def test_create_folder_fail(cloud: Dropbox, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/create_folder_v2",
        method="POST",
        json={"error_summary": "path/conflict/folder/."},
        status_code=httpx.codes.CONFLICT
    )
    with pytest.raises(Exception) as e_info:
        cloud.create_folder("/path/to/folder")
    assert e_info.value.args[0] == 'FolderConflictError. Не удалось создать папку, так как ресурс уже существует.'
