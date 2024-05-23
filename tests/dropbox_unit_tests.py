import zipfile
from os import path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from api_clients.dropbox import Dropbox


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


@pytest.mark.asyncio
async def test_get_cloud_info(cloud: Dropbox, httpx_mock: HTTPXMock):
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
    cloud_info = await cloud.get_cloud_info()
    assert cloud_info["name"] == "Test User" and cloud_info["login"] == "test_user@example.com" and cloud_info[
        "used_space"]


@pytest.mark.asyncio
async def test_get_folder_content_ok(cloud: Dropbox, httpx_mock: HTTPXMock):
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
    folder_content = await cloud.get_folder_content("")
    assert ["folder1"] == folder_content["folders"] and ["file1.txt"] == folder_content["files"]


@pytest.mark.asyncio
async def test_get_folder_content_fail_remote(cloud: Dropbox, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/get_metadata",
        method="POST",
        json={
            "error_summary": "path/not_found/."
        },
        status_code=httpx.codes.NOT_FOUND
    )

    with pytest.raises(Exception) as e_info:
        await cloud.get_folder_content("/acdcdcd")
    assert e_info.value.args[0] == 'NotFoundError. Не удалось найти запрошенный ресурс.'


@pytest.mark.asyncio
async def test_get_folder_content_fail_remote_not_folder(cloud: Dropbox, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/get_metadata",
        method="POST",
        json={
            ".tag": ".txt."
        }
    )
    with pytest.raises(Exception) as e_info:
        await cloud.get_folder_content("folder/file.docx")
    assert e_info.value.args[0] == 'NotAFolderError. Запрошенный ресурс не является папкой'


@pytest.mark.asyncio
async def test_download_file_ok(cloud: Dropbox, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/get_metadata",
        method="POST",
        json={
            ".tag": "file"
        }
    )
    httpx_mock.add_response(
        url="https://content.dropboxapi.com/2/files/download",
        method="POST",
        content=b"Hello, World!",
    )
    local_path = tmp_path / "file.txt"
    result = await cloud.download_file("/path/to/file.txt", str(local_path))
    assert result["status"] == "ok" and local_path.read_bytes() == b"Hello, World!"

@pytest.mark.asyncio
async def test_download_file_fail_remote(cloud: Dropbox, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/get_metadata",
        method="POST",
        json={
            "error_summary": "path/not_found/."
        },
        status_code=httpx.codes.NOT_FOUND
    )
    local_path = tmp_path / "file.txt"
    with pytest.raises(Exception) as e_info:
        await cloud.download_file("/path/to/file123.docx", str(local_path))
    assert e_info.value.args[0] == 'NotFoundError. Не удалось найти запрошенный ресурс.'


@pytest.mark.asyncio
async def test_download_file_fail_local(cloud: Dropbox, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/get_metadata",
        method="POST",
        json={
            ".tag": "file"
        }
    )
    httpx_mock.add_response(
        url="https://content.dropboxapi.com/2/files/download",
        method="POST",
        content=b"Hello, World!"
    )
    local_path = tmp_path / "abracad" / "file.txt"
    with pytest.raises(Exception) as e_info:
        await cloud.download_file("/path/to/file.txt", str(local_path))
    assert e_info.value.args[0] == f'FileNotFoundError. Неверный путь: {str(local_path)}'


@pytest.mark.asyncio
async def test_upload_file_ok(cloud: Dropbox, httpx_mock: HTTPXMock, tmp_path):
    local_path = tmp_path / "file.txt"
    local_path.write_bytes(b"Hello, World!")
    httpx_mock.add_response(
        url="https://content.dropboxapi.com/2/files/upload",
        method="POST",
        headers={
            "Dropbox-API-Arg": '{"path":"/path/to/file.txt","mode":"overwrite","autorename":true,"mute":false,"strict_conflict":false}'},
        status_code=httpx.codes.OK
    )
    result = await cloud.upload_file(str(local_path), "/path/to/file.txt")
    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_file_fail_local(cloud: Dropbox, tmpdir):
    folder_path = tmpdir.mkdir("test_folder")
    with pytest.raises(Exception) as e_info:
        await cloud.upload_file(str(folder_path), "/path/to/file.txt")
    assert e_info.value.args[0] == 'NotAFileError. Загружаемый ресурс не является файлом'


@pytest.mark.asyncio
async def test_upload_file_fail_local_not_exist_file(cloud, tmpdir):
    non_existent_file = tmpdir.join("non_existent_file.txt")

    with pytest.raises(Exception) as e_info:
        await cloud.upload_file(str(non_existent_file), "/path/to/file.txt")

    assert e_info.value.args[0] == f'FileNotFoundError. Файл не найден: {non_existent_file}'


@pytest.mark.asyncio
async def test_create_folder_fail(cloud: Dropbox, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/create_folder_v2",
        method="POST",
        json={"error_summary": "path/conflict/folder/."},
        status_code=httpx.codes.CONFLICT
    )
    with pytest.raises(Exception) as e_info:
        await cloud.create_folder("/path/to/folder")
    assert e_info.value.args[0] == 'FolderConflictError. Не удалось создать папку, так как ресурс уже существует.'


@pytest.mark.asyncio
async def test_download_folder_ok(cloud: Dropbox, httpx_mock: HTTPXMock, tmp_path):
    zip_file_path = tmp_path / "folder.zip"
    with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
        zip_file.writestr("test.txt", "abc")

    with open(zip_file_path, 'rb') as f:
        zip_content = f.read()

    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/get_metadata",
        method="POST",
        json={
            ".tag": "folder"
        }
    )
    httpx_mock.add_response(
        url="https://content.dropboxapi.com/2/files/download_zip",
        method="POST",
        content=zip_content,
    )

    local_path = tmp_path / "downloaded_folder"
    local_path.mkdir()

    result = await cloud.download_folder("/path/to/folder", str(local_path))
    assert result["status"] == "ok" and path.exists(local_path / "test.txt")


@pytest.mark.asyncio
async def test_download_folder_fail_remote(cloud: Dropbox, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url="https://api.dropboxapi.com/2/files/get_metadata",
        method="POST",
        json={
            ".tag": ".txt."
        }
    )
    with pytest.raises(Exception) as e_info:
        await cloud.get_folder_content("folder/file.docx")
    assert e_info.value.args[0] == 'NotAFolderError. Запрошенный ресурс не является папкой'



