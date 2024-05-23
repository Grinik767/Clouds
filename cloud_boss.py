import click
from system_class import SystemClass
from api_clients.yandex_disk import YandexDisk
from api_clients.dropbox import Dropbox
from os import getenv
import httpx


class CloudBoss:
    def __init__(self):
        SystemClass.load_env(dev=False)
        self.clouds = {"yandex": YandexDisk(getenv("AUTH_TOKEN_YANDEX")),
                       "dropbox": Dropbox(getenv("AUTH_TOKEN_DROPBOX"))}

    async def get_cloud_info(self, cloud_name: str):
        try:
            response = await self.clouds[cloud_name].get_cloud_info()
            click.echo(
                f"Логин:\t{response['login']}\nИмя:\t{response['name']}\n"
                f"Всего места:\t{round(response['total_space'], 3)} "
                f"MB\nИспользовано:\t{round(response['used_space'], 3)} MB")
        except httpx.HTTPError:
            click.echo("Произошла ошибка. Попробуйте позже.")

    async def get_folder_content(self, cloud_name: str, path_remote: str):
        try:
            response = await self.clouds[cloud_name].get_folder_content(path_remote)
            click.echo('\n'.join(map(lambda el: f"/{el}", response['folders'])))
            click.echo('\n'.join(response['files']))
        except httpx.HTTPError:
            click.echo("Произошла ошибка. Попробуйте позже.")

    async def create_folder(self, cloud_name: str, path_remote: str):
        try:
            await self.clouds[cloud_name].create_folder(path_remote)
            click.echo("Папка успешно создана!")
        except httpx.HTTPError:
            click.echo("Произошла ошибка. Попробуйте позже.")

    async def download(self, cloud_name: str, path_remote: str, path_local: str):
        try:
            await self.clouds[cloud_name].download_file(path_remote, path_local)
            click.echo("Файл успешно скачан!")
        except httpx.HTTPError:
            click.echo("Произошла ошибка. Попробуйте позже.")
        except Exception:
            try:
                await self.clouds[cloud_name].download_folder(path_remote, path_local)
                click.echo("Папка успешно скачана!")
            except Exception as e2:
                SystemClass.exchandler(type(e2), e2, e2.__traceback__)

    async def upload(self, cloud_name: str, path_local: str, path_remote: str):
        try:
            await self.clouds[cloud_name].upload_file(path_local, path_remote)
            click.echo("Файл успешно загружен!")
        except httpx.HTTPError:
            click.echo("Произошла ошибка. Попробуйте позже.")
        except Exception:
            try:
                await self.clouds[cloud_name].upload_folder(path_local, path_remote)
                click.echo("Папка успешно загружена!")
            except Exception as e2:
                SystemClass.exchandler(type(e2), e2, e2.__traceback__)
