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
