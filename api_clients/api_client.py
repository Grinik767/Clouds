from abc import ABC, abstractmethod


class Cloud(ABC):
    @abstractmethod
    def auth(self, auth_token: str) -> None:
        pass

    @abstractmethod
    def get_cloud_info(self) -> dict:
        pass

    @abstractmethod
    def get_folder_content(self, path: str) -> dict:
        pass

    @abstractmethod
    def download_file(self, path_remote: str, path_local: str) -> dict:
        pass

    @abstractmethod
    def upload_file(self, path_local: str, path_remote: str) -> dict:
        pass

    @abstractmethod
    def download_folder(self):
        pass

    def upload_folder(self):
        pass

    @abstractmethod
    def create_folder(self, path: str) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def error_worker(response: dict):
        pass
