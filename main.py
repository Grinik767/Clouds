from cloud_boss import CloudBoss
from os import getenv
import click


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = CloudBoss()


@cli.command()
@click.option('--cloud', type=click.Choice(['yandex', 'google'], case_sensitive=False),
              prompt='Выберите облако (Yandex/Google)', help='Выбор облака')
@click.pass_context
def info(ctx, cloud: str):
    """Получить информацию об облаке."""
    if cloud == "yandex":
        ctx.obj.get_cloud_info(cloud)
    else:
        pass


@cli.command()
@click.argument('path', default=lambda: getenv('DEFAULT_PATH_YANDEX'))
@click.option('--cloud', type=click.Choice(['yandex', 'google'], case_sensitive=False),
              prompt='Выберите облако (Yandex/Google)', help='Выбор облака')
@click.pass_context
def folder_content(ctx, path: str, cloud: str):
    """Получить содержимое папки в облаке."""
    if cloud == "yandex":
        ctx.obj.get_folder_content(cloud, path)
    else:
        pass


@cli.command()
@click.argument('path')
@click.option('--cloud', type=click.Choice(['yandex', 'google'], case_sensitive=False),
              prompt='Выберите облако (Yandex/Google)', help='Выбор облака')
@click.pass_context
def create_folder(ctx, path: str, cloud: str):
    """Создать папку в облаке."""
    if cloud == "yandex":
        ctx.obj.create_folder(cloud, path)
    else:
        pass


if __name__ == '__main__':
    cli()
