import zipfile
from os import path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from api_clients.yandex_disk import YandexDisk


@pytest.fixture
def cloud(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"https://cloud-api.yandex.net/v1/disk/",
        method="GET"
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


@pytest.mark.asyncio
async def test_get_cloud_info(cloud: YandexDisk, httpx_mock: HTTPXMock):
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
        }
    )
    cloud_info = await cloud.get_cloud_info()
    assert cloud_info["login"] == "test_user" and cloud_info["name"] == "Test User" and cloud_info[
        "total_space"] == 1024 and cloud_info["used_space"] == 512


@pytest.mark.asyncio
async def test_get_folder_content_ok(cloud: YandexDisk, httpx_mock: HTTPXMock):
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
        }
    )
    folder_content = await cloud.get_folder_content("/")
    assert ["folder1"] == folder_content["folders"] and ["file1.txt"] == folder_content["files"]


@pytest.mark.asyncio
async def test_get_folder_content_fail_remote(cloud: YandexDisk, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{cloud.url}resources?path=%2Fabracad&fields=type%2C_embedded.items.name%2C_embedded.items.type",
        method="GET",
        json={"error": "DiskNotFoundError", "message": "Не удалось найти запрошенный ресурс."},
        status_code=httpx.codes.NOT_FOUND
    )
    with pytest.raises(Exception) as e_info:
        await cloud.get_folder_content("/abracad")
    assert e_info.value.args[0] == 'DiskNotFoundError. Не удалось найти запрошенный ресурс.'


@pytest.mark.asyncio
async def test_get_folder_content_fail_remote_not_folder(cloud: YandexDisk, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{cloud.url}resources?path=folder%2Ffile.docx&fields=type%2C_embedded.items.name%2C_embedded.items.type",
        method="GET",
        json={
            "type": "file",
        }
    )
    with pytest.raises(Exception) as e_info:
        await cloud.get_folder_content("folder/file.docx")
    assert e_info.value.args[0] == 'NotAFolder. Запрошенный ресурс не является папкой'


@pytest.mark.asyncio
async def test_download_file_ok(cloud: YandexDisk, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url=f"{cloud.url}resources/download?path=%2Fpath%2Fto%2Ffile.txt&fields=href",
        method="GET",
        json={"href": "https://download.example.com/file.txt"}
    )
    httpx_mock.add_response(
        url=f"{cloud.url}resources?path=%2Fpath%2Fto%2Ffile.txt&fields=type%2C_embedded.items.name%2C_embedded.items.type",
        method="GET",
        json={"type": "file"}
    )
    httpx_mock.add_response(
        url="https://download.example.com/file.txt",
        content=b"Hello, World!",
        method="GET"
    )
    local_path = tmp_path / "file.txt"
    result = await cloud.download_file("/path/to/file.txt", str(local_path))
    assert result["status"] == "ok" and local_path.read_bytes() == b"Hello, World!"


@pytest.mark.asyncio
async def test_download_file_fail_remote(cloud: YandexDisk, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url=f"{cloud.url}resources/download?path=folder%2Ffile123.docx&fields=href",
        method="GET",
        json={"error": "DiskNotFoundError", "message": "Не удалось найти запрошенный ресурс."},
        status_code=httpx.codes.NOT_FOUND)
    local_path = tmp_path / "file.txt"
    with pytest.raises(Exception) as e_info:
        await cloud.download_file("folder/file123.docx", str(local_path))
    assert e_info.value.args[0] == 'DiskNotFoundError. Не удалось найти запрошенный ресурс.'


@pytest.mark.asyncio
async def test_download_file_fail_local(cloud: YandexDisk, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url=f"{cloud.url}resources/download?path=%2Fpath%2Fto%2Ffile.txt&fields=href",
        method="GET",
        json={"href": "https://download.example.com/file.txt"}
    )
    httpx_mock.add_response(
        url=f"{cloud.url}resources?path=%2Fpath%2Fto%2Ffile.txt&fields=type%2C_embedded.items.name%2C_embedded.items.type",
        method="GET",
        json={"type": "file"}
    )
    httpx_mock.add_response(
        url="https://download.example.com/file.txt",
        content=b"Hello, World!",
        method="GET"
    )
    local_path = tmp_path / "abracad" / "file.txt"
    with pytest.raises(Exception) as e_info:
        await cloud.download_file("/path/to/file.txt", str(local_path))
    assert e_info.value.args[0] == f'FileNotFoundError. Неверный путь: {str(local_path)}'


@pytest.mark.asyncio
async def test_upload_file_ok(cloud: YandexDisk, httpx_mock: HTTPXMock, tmp_path):
    local_path = tmp_path / "file.txt"
    local_path.write_bytes(b"Hello, World!")
    httpx_mock.add_response(
        url=f"{cloud.url}resources/upload?path=%2Fpath%2Fto%2Ffile.txt&fields=href&overwrite=true",
        json={"href": "https://upload.example.com/file.txt"},
        method="GET"
    )
    httpx_mock.add_response(
        url="https://upload.example.com/file.txt",
        status_code=httpx.codes.CREATED,

    )
    result = await cloud.upload_file(str(local_path), "/path/to/file.txt")
    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_file_fail_local(cloud: YandexDisk, tmpdir):
    folder_path = tmpdir.mkdir("test_folder")
    with pytest.raises(Exception) as e_info:
        await cloud.upload_file(str(folder_path), "/path/to/file.txt")
    assert e_info.value.args[0] == 'NotAFile. Загружаемый ресурс не является файлом'


@pytest.mark.asyncio
async def test_create_folder_ok(cloud: YandexDisk, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{cloud.url}resources?path=%2Fpath%2Fto%2Ffolder",
        method="PUT",
        status_code=httpx.codes.CREATED
    )
    result = await cloud.create_folder("/path/to/folder")
    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_create_folder_fail(cloud: YandexDisk, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{cloud.url}resources?path=%2Fpath%2Fto%2Ffolder",
        method="PUT",
        json={"error": "DiskNotFoundError", "message": "Не удалось найти запрошенный ресурс."},
        status_code=httpx.codes.NOT_FOUND
    )
    with pytest.raises(Exception) as e_info:
        await cloud.create_folder("/path/to/folder")
    assert e_info.value.args[0] == 'DiskNotFoundError. Не удалось найти запрошенный ресурс.'


@pytest.mark.asyncio
async def test_download_folder_ok(cloud: YandexDisk, httpx_mock: HTTPXMock, tmp_path):
    zip_file_path = tmp_path / "folder.zip"
    with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
        zip_file.writestr("test.txt", "abc")

    with open(zip_file_path, 'rb') as f:
        zip_content = f.read()

    httpx_mock.add_response(
        url=f"{cloud.url}resources/download?path=%2Fpath%2Fto%2Ffolder&fields=href",
        json={"href": "https://download.example.com/folder.zip"}
    )
    httpx_mock.add_response(
        url=f"{cloud.url}resources?path=%2Fpath%2Fto%2Ffolder&fields=type%2C_embedded.items.name%2C_embedded.items.type",
        json={"type": "dir"}
    )
    httpx_mock.add_response(
        url="https://download.example.com/folder.zip",
        content=zip_content
    )

    local_path = tmp_path / "downloaded_folder"
    local_path.mkdir()

    result = await cloud.download_folder("/path/to/folder", str(local_path))
    assert result["status"] == "ok" and path.exists(local_path / "test.txt")


@pytest.mark.asyncio
async def test_download_folder_fail_remote(cloud: YandexDisk, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url=f"{cloud.url}resources/download?path=%2Fpath%2Fto%2Fnonexistent_folder&fields=href",
        json={"error": "DiskNotFoundError", "message": "Не удалось найти запрошенный ресурс."},
        status_code=httpx.codes.NOT_FOUND
    )

    local_path = tmp_path / "downloaded_folder"
    local_path.mkdir()

    with pytest.raises(Exception) as e_info:
        await cloud.download_folder("/path/to/nonexistent_folder", str(local_path))
    assert e_info.value.args[0] == 'DiskNotFoundError. Не удалось найти запрошенный ресурс.'


@pytest.mark.asyncio
async def test_download_folder_fail_remote_finish(cloud: YandexDisk, httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url=f"{cloud.url}resources/download?path=%2Fpath%2Fto%2Ffolder&fields=href",
        json={"href": "https://download.example.com/folder.zip"}
    )
    httpx_mock.add_response(
        url=f"{cloud.url}resources?path=%2Fpath%2Fto%2Ffolder&fields=type%2C_embedded.items.name%2C_embedded.items.type",
        json={"type": "dir"}
    )
    httpx_mock.add_response(
        url="https://download.example.com/folder.zip",
        status_code=404
    )

    local_path = tmp_path / "downloaded_folder"
    local_path.mkdir()

    with pytest.raises(Exception) as e_info:
        await cloud.download_folder("/path/to/folder", str(local_path))
    assert e_info.value.args[
               0] == "FolderDownloadError. Не возможно скачать папку /path/to/folder"
