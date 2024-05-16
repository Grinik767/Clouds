from api_client import Cloud
from system_class import SystemClass
from os import path, getenv
import httpx


class YandexDisk(Cloud):
    def __init__(self, auth_token: str) -> None:
        self.session = None
        self.url = "https://cloud-api.yandex.net/v1/disk/"
        self.auth(auth_token)

    def auth(self, auth_token: str) -> None:
        r = httpx.get(self.url, headers={"Authorization": auth_token})
        if r.status_code != httpx.codes.OK:
            self.error_worker(
                {"error": "AuthError", "message": "Ошибка авторизации в Яндекс.Диске. Проверьте/обновите данные"})
        self.session = httpx.Client(headers={"Authorization": auth_token})

    def get_cloud_info(self) -> dict:
        with self.session:
            r = self.session.get(self.url, params={"fields": "user.login,user.display_name,total_space,used_space"})
        if r.status_code != httpx.codes.OK:
            return self.error_worker(r.json())
        answer = r.json()
        return {"login": answer["user"]["login"], "name": answer["user"]["display_name"],
                "total_space": answer["total_space"] / (2 ** 20),
                "used_space": answer["used_space"] / (2 ** 20)}

    def get_folder_content(self, path: str) -> dict:
        with self.session:
            r = self.session.get(f"{self.url}resources",
                                 params={"path": path, "fields": "type,_embedded.items.name,_embedded.items.type"})
        answer = r.json()
        if r.status_code != httpx.codes.OK:
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
                {"error": "FileNotFoundError", "message": f"Неверный путь: {path.abspath(path_local)}"})

    def upload_file(self, path_local: str, path_remote: str) -> dict:
        if not path.isfile(path_local):
            return self.error_worker({"error": "NotAFile", "message": "Загружаемый ресурс не является файлом"})
        with self.session:
            r = self.session.get(f"{self.url}resources/upload",
                                 params={"path": path_remote, "fields": "href", "overwrite": True})
            if r.status_code != 200:
                return self.error_worker(r.json())
            with open(path.abspath(path_local), 'rb') as data:
                r = self.session.put(r.json()["href"], content=data)
            if r.status_code == 201:
                return {"status": "ok"}
            return self.error_worker(r.json())

    def create_folder(self, path: str) -> dict:
        with self.session:
            r = self.session.put(f"{self.url}resources", params={"path": path})
        if r.status_code == 201:
            return {"status": "ok"}
        return self.error_worker(r.json())

    # just for unit tests
    def delete_folder(self, path: str) -> None:
        httpx.delete(f"{self.url}resources", headers={"Authorization": getenv("DEV_AUTH_TOKEN_YANDEX")},
                     params={"path": path, "force_async": True,
                             "permanently": True})

    @staticmethod
    def error_worker(response: dict):
        with SystemClass.except_handler(SystemClass.exchandler):
            raise Exception(f"{response['error']}. {response['message']}")


if __name__ == '__main__':
    pass
