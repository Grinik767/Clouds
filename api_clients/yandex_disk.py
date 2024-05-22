import os
from os import path
import asyncio
import aiofiles
import httpx

from system_class import SystemClass

from api_client import Cloud


class YandexDisk(Cloud):

    def __init__(self, auth_token: str):
        self.headers = None
        self.url = "https://cloud-api.yandex.net/v1/disk/"
        self.auth(auth_token)

    def auth(self, auth_token: str) -> None:
        r = httpx.get(self.url, headers={"Authorization": auth_token})
        if r.is_error:
            self.error_worker(
                {"error": "AuthError", "message": "Ошибка авторизации в Яндекс.Диске. Проверьте/обновите данные"})
        self.headers = {"Authorization": auth_token}

    async def get_cloud_info(self) -> dict:
        async with httpx.AsyncClient(headers=self.headers) as session:
            r = await session.get(self.url,
                                  params={"fields": "user.login,user.display_name,total_space,used_space"})
        answer = r.json()
        if r.is_error:
            return self.error_worker(answer)
        return {"login": answer["user"]["login"], "name": answer["user"]["display_name"],
                "total_space": answer["total_space"] / (2 ** 20),
                "used_space": answer["used_space"] / (2 ** 20)}

    async def get_folder_content(self, path: str) -> dict:
        async with httpx.AsyncClient(headers=self.headers) as session:
            r = await session.get(f"{self.url}resources",
                                  params={"path": path, "fields": "type,_embedded.items.name,_embedded.items.type"})
        answer = r.json()
        if r.is_error:
            return self.error_worker(answer)
        if answer["type"] != "dir":
            return self.error_worker({"error": "NotAFolder", "message": "Запрошенный ресурс не является папкой"})
        files = []
        folders = []
        for item in answer["_embedded"]["items"]:
            if item["type"] == "dir":
                folders.append(item["name"])
            else:
                files.append(item["name"])
        return {"folders": folders, "files": files}

    async def download_file(self, path_remote: str, path_local: str) -> dict:
        async with httpx.AsyncClient(headers=self.headers) as session:
            r = await session.get(f"{self.url}resources/download", params={"path": path_remote, "fields": "href"})
            if r.is_error:
                return self.error_worker(r.json())
            r_type = await session.get(f"{self.url}resources", params={"path": path_remote,
                                                                       "fields": "type,_embedded.items.name,_embedded.items.type"})
            if r_type.json()["type"] != "file":
                return self.error_worker({"error": "NotAFile", "message": "Запрошенный ресурс не является файлом"})
            response = await session.get(r.json()["href"], follow_redirects=True)
        if response.is_error:
            return self.error_worker(
                {"error": "FileDownloadError", "message": f"Не возможно скачать файл {path_remote}"})
        try:
            async with aiofiles.open(path.abspath(path_local), 'wb') as file:
                await file.write(response.content)
            return {"status": "ok"}
        except FileNotFoundError:
            return self.error_worker(
                {"error": "FileNotFoundError", "message": f"Неверный путь: {path.abspath(path_local)}"})

    async def upload_file(self, path_local: str, path_remote: str) -> dict:
        if not path.isfile(path_local):
            return self.error_worker({"error": "NotAFile", "message": "Загружаемый ресурс не является файлом"})
        async with httpx.AsyncClient(headers=self.headers) as session:
            r = await session.get(f"{self.url}resources/upload",
                                  params={"path": path_remote, "fields": "href", "overwrite": True})
            answer = r.json()
            if r.is_error:
                return self.error_worker(answer)
            async with aiofiles.open(path.abspath(path_local), 'rb') as data:
                r = await session.put(answer["href"], content=data)
        if r.is_error:
            return self.error_worker(r.json())
        return {"status": "ok"}

    async def create_folder(self, path: str) -> dict:
        async with httpx.AsyncClient(headers=self.headers) as session:
            r = await session.put(f"{self.url}resources", params={"path": path})
        if r.is_error:
            return self.error_worker(r.json())
        return {"status": "ok"}

    def download_folder(self):
        pass

    @staticmethod
    def error_worker(response: dict):
        with SystemClass.except_handler(SystemClass.exchandler):
            raise Exception(f"{response['error']}. {response['message']}")


if __name__ == '__main__':
    SystemClass.load_env()
    cloud = YandexDisk(os.getenv("AUTH_TOKEN_YANDEX"))
    asyncio.run(cloud.upload_folder("C:/Users/grigo/Desktop/Clouds/for_tests", "tests"))
