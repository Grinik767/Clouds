from abc import ABC, abstractmethod
from os import path, walk


class Cloud(ABC):
    @abstractmethod
    def auth(self, auth_token: str) -> None:
        pass

    @abstractmethod
    async def get_cloud_info(self) -> dict:
        pass

    @abstractmethod
    async def get_folder_content(self, path_remote: str) -> dict:
        pass

    @abstractmethod
    async def download_file(self, path_remote: str, path_local: str) -> dict:
        pass

    @abstractmethod
    async def upload_file(self, path_local: str, path_remote: str) -> dict:
        pass

    @abstractmethod
    async def download_folder(self, path_remote: str, path_local: str) -> dict:
        pass

    async def upload_folder(self, path_local: str, path_remote: str) -> dict:
        local_path = path.abspath(path_local)
        await self.try_to_create_folder(path_remote)
        for root, dirs, files in walk(local_path):
            for directory in dirs:
                dir_local = path.join(root, directory)
                dir_remote = path.join(path_remote, path.relpath(dir_local, local_path)).replace("\\", "/")
                await self.try_to_create_folder(dir_remote)

            for file in files:
                file_local = path.join(root, file)
                file_remote = path.join(path_remote, path.relpath(file_local, local_path)).replace("\\", "/")
                await self.upload_file(file_local, file_remote)

        return {"status": "ok"}

    async def try_to_create_folder(self, path_remote: str) -> None:
        try:
            await self.create_folder(path_remote)
        except Exception:
            pass

    @abstractmethod
    async def create_folder(self, path_remote: str) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def error_worker(response: dict):
        pass
