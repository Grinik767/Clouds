import asyncio
import json
import os
import zipfile
from os import path

import aiofiles
import httpx

from system_class import SystemClass

from api_client import Cloud


class Dropbox(Cloud):

    def __init__(self, auth_token: str) -> None:
        self.headers = None
        self.url = "https://api.dropboxapi.com/2/"
        self.auth(auth_token)
        self.auth_token = auth_token

    def auth(self, auth_token: str) -> None:
        r = httpx.post(f"{self.url}users/get_current_account", headers={"Authorization": f"Bearer {auth_token}"})
        if r.status_code != 200:
            self.error_worker(
                {"error": {".tag": "AuthError"},
                 "error_summary": "Ошибка авторизации в Dropbox. Проверьте/обновите данные"})
        self.headers = {"Authorization": auth_token}

    async def get_cloud_info(self) -> dict:
        async with httpx.AsyncClient(headers=self.headers) as session:
            r = await session.post(f"{self.url}users/get_space_usage",
                                   headers={"Authorization": f"Bearer {self.auth_token}"})
            if r.status_code != 200:
                return self.add_error(r)
            used_space = r.json()["used"]
            r = await session.post(f"{self.url}users/get_current_account",
                                   headers={"Authorization": f"Bearer {self.auth_token}"})
            if r.status_code != httpx.codes.OK:
                return self.add_error(r)
            usage_info = r.json()
            return {
                "name": usage_info["name"]["display_name"],
                "login": usage_info["email"],
                "used_space": used_space / 2 ** 20,
                "total_space": -1
            }

    async def get_folder_content(self, path_remote: str) -> dict:
        async with httpx.AsyncClient(headers=self.headers) as session:
            headers = {"Authorization": f"Bearer {self.auth_token}",
                       "Content-Type": "application/json"}
            r = await session.post(f"{self.url}files/get_metadata", headers=headers,
                                   json={"include_deleted": False, "include_has_explicit_shared_members": False,
                                         "include_media_info": False, "path": f"{path_remote}"
                                         })
            if r.status_code != 200:
                return self.error_worker(
                    {"error": {".tag": "NotFoundError"}, "error_summary": "Не удалось найти запрошенный ресурс."})
            if r.json()['.tag'] != "folder":
                return self.error_worker(
                    {"error": {".tag": "NotAFolderError"}, "error_summary": "Запрошенный ресурс не является папкой"})

            r = await session.post(f"{self.url}files/list_folder",
                                   json={"path": f"{path_remote}", "recursive": False, "include_media_info": False,
                                         "include_deleted": False, "include_has_explicit_shared_members": False
                                         }, headers=headers)
            if r.status_code != 200:
                return self.add_error(r)

            content_info = r.json()
            files = [entry["name"] for entry in content_info["entries"] if
                     isinstance(entry, dict) and entry[".tag"] == "file"]
            folders = [entry["name"] for entry in content_info["entries"] if
                       isinstance(entry, dict) and entry[".tag"] == "folder"]
            return {"folders": folders, "files": files}

    async def download(self, path_remote: str, is_file: bool = True) -> bytes:
        async with httpx.AsyncClient(headers=self.headers) as session:
            headers = {"Authorization": f"Bearer {self.auth_token}",
                       "Content-Type": "application/json"}
            r = await session.post(f"{self.url}files/get_metadata", headers=headers,
                                   json={"include_deleted": False, "include_has_explicit_shared_members": False,
                                         "include_media_info": False, "path": f"{path_remote}"
                                         })
            if r.status_code != 200:
                return self.error_worker(
                    {"error": {".tag": "NotFoundError"}, "error_summary": "Не удалось найти запрошенный ресурс."})
            resp = r.json()
            if resp['.tag'] == "folder" and is_file:
                return self.error_worker(
                    {"error": {".tag": "NotAFileError"}, "error_summary": "Запрошенный ресурс не является файлом"})
            elif resp['.tag'] != "folder" and not is_file:
                return self.error_worker(
                    {"error": {".tag": "NotAFolderError"}, "error_summary": "Запрошенный ресурс не является папкой"})
            dropbox_api_arg = json.dumps({"path": f"{path_remote}"})

            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Dropbox-API-Arg": dropbox_api_arg
            }
            r = None
            if is_file:
                r = await session.post(f"https://content.dropboxapi.com/2/files/download", headers=headers)
            else:
                r = await session.post(f"https://content.dropboxapi.com/2/files/download_zip", headers=headers)
            if r.status_code != 200:
                return self.add_error(r)
            return r.content

    async def download_file(self, path_remote: str, path_local: str) -> dict:
        if path.isdir(path.abspath(path_local)):
            return self.error_worker(
                {"error": "FileNotFoundError", "message": f"Неверный путь: {path.abspath(path_local)}"})
        await self.save_file(path_local, await self.download(path_remote))
        return {"status": "ok"}

    async def download_folder(self, path_remote: str, path_local: str) -> dict:
        if path.isfile(path.abspath(path_local)):
            return self.error_worker(
                {"error": "FolderNotFoundError", "message": f"Неверный путь: {path.abspath(path_local)}"})
        path_to_zip = path.join(path.abspath(path_local), "archive.zip")
        await self.save_file(path_to_zip, await self.download(path_remote, is_file=False))
        with zipfile.ZipFile(path_to_zip) as zip_ref:
            zip_ref.extractall(path_local)
        os.remove(path_to_zip)
        return {"status": "ok"}

    async def save_file(self, path_local: str, content: bytes):
        try:
            async with aiofiles.open(path.abspath(path_local), 'wb') as file:
                await file.write(content)
        except FileNotFoundError:
            return self.error_worker(
                {"error": {".tag": "FileNotFoundError"}, "message": f"Неверный путь: {path.abspath(path_local)}"})

    async def upload_file(self, path_local: str, path_remote: str) -> dict:
        async with httpx.AsyncClient(headers=self.headers) as session:
            data = {
                "path": f"{path_remote}",
                "mode": "add",
                "autorename": True,
                "mute": False
            }
            try:
                if path.isdir(path_local):
                    return self.error_worker(
                        {"error": {".tag": "NotAFileError"}, "error_summary": "Загружаемый ресурс не является файлом"})
                with open(path_local, "rb") as f:
                    headers = {
                        "Authorization": f"Bearer {self.auth_token}",
                        "Dropbox-API-Arg": json.dumps(data),
                        "Content-Type": "application/octet-stream"
                    }
                    r = await session.post("https://content.dropboxapi.com/2/files/upload", headers=headers,
                                           content=f.read())
                    if r.status_code != 200:
                        return self.add_error(r)
            except FileNotFoundError:
                return self.error_worker({
                    "error": {".tag": "FileNotFoundError"},
                    "error_summary": f"Файл не найден: {path_local}"
                })

            if r.status_code == 200:
                return {"status": "ok"}
            else:
                return self.add_error(r)

    async def create_folder(self, path_remote: str) -> dict:
        async with httpx.AsyncClient(headers=self.headers) as session:
            data = {"path": f"{path_remote}", "autorename": False}
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            r = await session.post("https://api.dropboxapi.com/2/files/create_folder_v2", json=data, headers=headers)
            if r.status_code == 200:
                return {"status": "ok"}
            else:
                if r.status_code == 409:
                    return self.error_worker({"error": {".tag": "FolderConflictError"},
                                              "error_summary": "Не удалось создать папку, так как ресурс уже "
                                                               "существует."})
                return self.add_error(r)

    @staticmethod
    def error_worker(response: dict):
        with SystemClass.except_handler(SystemClass.exchandler):
            raise Exception(f"{response['error']['.tag']}. {response['error_summary']}")

    @staticmethod
    def add_error(response: httpx.Response):
        try:
            return Dropbox.error_worker(response.json())
        except json.JSONDecodeError:
            return Dropbox.error_worker({"error": {".tag": "Error"}, "error_summary": f"{response.status_code}"})


if __name__ == '__main__':
    pass
