import asyncio
from abc import ABC, abstractmethod
from os import path, walk

import httpx

from system_class import SystemClass


class Cloud(ABC):
    @abstractmethod
    def auth(self, auth_token: str) -> httpx.AsyncClient:
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

    async def create_sub_folders(self, path_local: str, path_remote: str) -> None:
        for root, dirs, files in walk(path_local):
            tasks = []
            for directory in dirs:
                dir_local = path.join(root, directory)
                dir_remote = path.join(path_remote, path.relpath(dir_local, path_local)).replace("\\", "/")
                tasks.append(self.try_to_create_folder(dir_remote))
            with SystemClass.except_handler(SystemClass.exchandler):
                await asyncio.gather(*tasks)

    async def upload_folder(self, path_local: str, path_remote: str) -> dict:
        local_path = path.abspath(path_local)
        await self.try_to_create_folder(path_remote)
        await self.create_sub_folders(local_path, path_remote)
        tasks = []
        for root, dirs, files in walk(local_path):
            for file in files:
                file_local = path.join(root, file)
                file_remote = path.join(path_remote, path.relpath(file_local, local_path)).replace("\\", "/")
                tasks.append(self.upload_file(file_local, file_remote))
        with SystemClass.except_handler(SystemClass.exchandler):
            await asyncio.gather(*tasks)

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
