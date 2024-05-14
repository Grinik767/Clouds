from abc import ABC, abstractmethod


class Cloud(ABC):
    @abstractmethod
    def auth(self, auth_token: str) -> None:
        pass

    @abstractmethod
    def configure(self, path_remote: str, path_local: str):
        pass

    @abstractmethod
    def get_disk_info(self):
        pass

    @abstractmethod
    def get_folder_content(self, path: str):
        pass

    @abstractmethod
    def download_file(self, path_remote: str, path_local: str):
        pass

    @abstractmethod
    def upload_file(self, path_local: str, path_remote: str):
        pass

    def download_folder(self):
        pass

    def upload_folder(self):
        pass

    @abstractmethod
    def create_folder(self, name: str):
        pass

    @staticmethod
    @abstractmethod
    def error_worker(response: dict) -> dict:
        pass
