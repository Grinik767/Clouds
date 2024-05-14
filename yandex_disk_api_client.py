from api_client import Cloud
from system_class import SystemClass
from os import getenv, path
import httpx


class YandexDisk(Cloud):
    def __init__(self, auth_token: str) -> None:
        self.headers = None
        self.default_path_remote = "/"
        self.default_path_local = path.dirname(__file__)
        self.url = "https://cloud-api.yandex.net/v1/disk/"
        self.auth(auth_token)

    def auth(self, auth_token: str) -> None:
        r = httpx.get(self.url, headers={"Authorization": auth_token})
        if r.status_code == 200:
            self.headers = {"Authorization": auth_token}
            return
        raise Exception("Ошибка аутентификации в Яндекс.Диске. Проверьте/обновите данные")

    def configure(self, path_remote: str, path_local: str):
        r = httpx.get(f"{self.url}resources", headers=self.headers,
                      params={"path": path_remote, "fields": "type"})
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
        r = httpx.get(self.url, headers=self.headers,
                      params={"fields": "user.login,user.display_name,total_space,used_space"})
        if r.status_code != 200:
            return self.error_worker(r.json())
        answer = r.json()
        return {"login": answer["user"]["login"], "name": answer["user"]["display_name"],
                "total_space": answer["total_space"] / (2 ** 20),
                "used_space": answer["used_space"] / (2 ** 20)}

    def get_folder_content(self, path: str):
        pass

    def download_file(self, path_remote: str, path_local: str):
        pass

    def upload_file(self, path_local: str, path_remote: str):
        pass

    def create_folder(self, name: str):
        pass

    @staticmethod
    def error_worker(response: dict) -> dict:
        return {"error": response["error"], "message": response["message"]}


if __name__ == '__main__':
    SystemClass.load_env()
    cloud = YandexDisk(getenv("DEV_AUTH_TOKEN"))
