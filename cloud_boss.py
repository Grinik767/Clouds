import click
from system_class import SystemClass
from yandex_disk_tests import YandexDisk
from os import getenv
import httpx


class CloudBoss:
    def __init__(self):
        SystemClass.load_env(dev=False)
        self.clouds = {"yandex": YandexDisk(getenv("AUTH_TOKEN_YANDEX"))}

    def get_cloud_info(self, cloud_name: str):
        try:
            response = self.clouds[cloud_name].get_cloud_info()
            click.echo(
                f"Логин:\t{response['login']}\nИмя:\t{response['name']}\n"
                f"Всего места:\t{round(response['total_space'], 3)} "
                f"MB\nИспользовано:\t{round(response['used_space'], 3)} MB")
        except httpx.HTTPError:
            click.echo("Произошла ошибка. Попробуйте позже.")

    def get_folder_content(self, cloud_name: str, path: str):
        try:
            response = self.clouds[cloud_name].get_folder_content(path)
            click.echo('\n'.join(map(lambda el: f"/{el}", response['folders'])))
            click.echo('\n'.join(response['files']))
        except httpx.HTTPError:
            click.echo("Произошла ошибка. Попробуйте позже.")

    def create_folder(self, cloud_name: str, path: str):
        try:
            self.clouds[cloud_name].create_folder(path)
            click.echo("Папка успешно создана!")
        except httpx.HTTPError:
            click.echo("Произошла ошибка. Попробуйте позже.")

    def download_file(self, cloud_name: str, path_remote: str, path_local: str):
        try:
            self.clouds[cloud_name].download_file(path_remote, path_local)
            click.echo("Файл успешно скачан!")
        except httpx.HTTPError:
            click.echo("Произошла ошибка. Попробуйте позже.")
