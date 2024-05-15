from cloud_boss import CloudBoss
from os import getenv
import click

cloud_boss = CloudBoss()


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = CloudBoss()


@cli.command()
@click.option('--cloud', type=click.Choice(['yandex', 'google'], case_sensitive=False),
              prompt='Выберите облако (Yandex/Google)', help='Выбор облака для работы')
@click.pass_context
def info(ctx, cloud: str):
    """Получить информацию об облаке."""
    if cloud == "yandex":
        ctx.obj.get_cloud_info("yandex")
    else:
        pass


if __name__ == '__main__':
    cli()
