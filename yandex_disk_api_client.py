from api_client import Cloud
from system_class import SystemClass
from os import getenv
import httpx


class YandexDisk(Cloud):
    def __init__(self, auth_token: str) -> None:
        self.headers = None
        self.url = "https://cloud-api.yandex.net/v1/disk/"
        self.auth(auth_token)

    def auth(self, auth_token: str) -> None:
        r = httpx.get(self.url, headers={"Authorization": auth_token})
        if r.status_code == 200:
            self.headers = {"Authorization": auth_token}
            return
        raise Exception("Ошибка аутентификации в Яндекс.Диске. Проверьте/обновите данные.")

    def configure(self):
        pass

    def get_disk_info(self):
        pass

    def get_folder_content(self, path: str):
        pass

    def download_file(self, path: str):
        pass

    def upload_file(self, path_local: str, path_remote: str):
        pass

    def create_folder(self, name: str):
        pass


if __name__ == '__main__':
    SystemClass.load_env()
    cloud = YandexDisk(getenv("DEV_AUTH_TOKEN"))
