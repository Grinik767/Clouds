from abc import ABC, abstractmethod


class Cloud(ABC):
    @abstractmethod
    def auth(self, auth_token: str) -> None:
        pass

    @abstractmethod
    def configure(self):
        pass

    @abstractmethod
    def get_disk_info(self):
        pass

    @abstractmethod
    def get_folder_content(self, path: str):
        pass

    @abstractmethod
    def download_file(self, path: str):
        pass

    @abstractmethod
    def upload_file(self, path_local: str, path_remote: str):
        pass

    @abstractmethod
    def create_folder(self, name: str):
        pass
