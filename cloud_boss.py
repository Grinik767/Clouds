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
            print(f"Login:\t{response['login']}")
            click.echo(f"Name:\t{response['name']}")
            click.echo(f"Total space:\t{response['total_space']} MB")
            click.echo(f"Used space:\t{response['used_space']} MB")
        except httpx.HTTPError:
            click.echo("Произошла ошибка. Попробуйте позже.")


if __name__ == '__main__':
    cloud_boss = CloudBoss()
    cloud_boss.get_cloud_info("yandex")
