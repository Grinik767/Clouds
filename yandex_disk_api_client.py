import os

from api_client import Cloud
from system_class import SystemClass
from os import getenv, path
import httpx


class YandexDisk(Cloud):
    def __init__(self, auth_token: str) -> None:
        self.session = None
        self.default_path_remote = "/"
        self.default_path_local = path.dirname(__file__)
        self.url = "https://cloud-api.yandex.net/v1/disk/"
        self.auth(auth_token)

    def auth(self, auth_token: str) -> None:
        r = httpx.get(self.url, headers={"Authorization": auth_token})
        if r.status_code == 200:
            self.session = httpx.Client()
            self.session.headers = {"Authorization": auth_token}
            return
        raise Exception("Ошибка авторизации в Яндекс.Диске. Проверьте/обновите данные")

    def configure(self, path_remote: str, path_local: str) -> None:
        with self.session:
            r = self.session.get(f"{self.url}resources", params={"path": path_remote, "fields": "type"})
        if r.status_code == 200:
            if r.json()["type"] == "dir":
                self.default_path_remote = path_remote
            else:
                raise Exception("Указанный путь не является папкой")
        else:
            raise Exception("Ошибка доступа к удаленной папке")
        if path.isdir(path_local):
            self.default_path_local = path.dirname(path.abspath(path_local))
            return
        raise Exception("Указанный локальный путь не является папкой")

    def get_disk_info(self) -> dict:
        with self.session:
            r = self.session.get(self.url, params={"fields": "user.login,user.display_name,total_space,used_space"})
        if r.status_code != 200:
            return self.error_worker(r.json())
        answer = r.json()
        return {"login": answer["user"]["login"], "name": answer["user"]["display_name"],
                "total_space": answer["total_space"] / (2 ** 20),
                "used_space": answer["used_space"] / (2 ** 20)}

    def get_folder_content(self, path: str) -> dict:
        if len(path) == 0:
            path = self.default_path_remote
        with self.session:
            r = self.session.get(f"{self.url}resources",
                                 params={"path": path, "fields": "type,_embedded.items.name,_embedded.items.type"})
        answer = r.json()
        if r.status_code != 200:
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

    def download_file(self, path_remote: str, path_local: str) -> dict:
        with self.session:
            r = self.session.get(f"{self.url}resources/download", params={"path": path_remote, "fields": "href"})
            if r.status_code != 200:
                return self.error_worker(r.json())
            r_type = self.session.get(f"{self.url}resources", params={"path": path_remote,
                                                                      "fields": "type,_embedded.items.name,_embedded.items.type"})
        if r_type.json()["type"] != "file":
            return self.error_worker({"error": "NotAFile", "message": "Запрошенный ресурс не является файлом"})
        response = httpx.get(r.json()["href"], follow_redirects=True)
        if response.status_code != 200:
            return self.error_worker(
                {"error": "FileDownloadError", "message": f"Не возможно скачать файл {path_remote}"})
        try:
            with open(path.abspath(path_local), 'wb') as file:
                file.write(response.content)
            return {"status": "ok"}
        except FileNotFoundError:
            return self.error_worker(
                {"error": "FileNotFoundError", "message": f"Не существует пути: {path.abspath(path_local)}"})

    def upload_file(self, path_local: str, path_remote: str):
        if not path.isfile(path_local):
            return self.error_worker({"error": "NotAFile", "message": "Загружаемый ресурс не является файлом"})
        with self.session:
            r = self.session.get(f"{self.url}resources/upload",
                                 params={"path": path_remote, "fields": "href", "overwrite": True})
        if r.status_code != 200:
            return self.error_worker(r.json())

    def create_folder(self, path: str) -> dict:
        with self.session:
            r = self.session.put(f"{self.url}resources", params={"path": path})
        if r.status_code == 201:
            return {"status": "ok"}
        return self.error_worker(r.json())

    # just for unit tests
    def delete_folder(self, path: str) -> None:
        httpx.delete(f"{self.url}resources", headers={"Authorization": os.getenv("DEV_AUTH_TOKEN")},
                     params={"path": path, "force_async": True,
                             "permanently": True})

    @staticmethod
    def error_worker(response: dict) -> dict:
        return {"error": response["error"], "message": response["message"]}


if __name__ == '__main__':
    SystemClass.load_env()
    cloud = YandexDisk(getenv("DEV_AUTH_TOKEN"))
