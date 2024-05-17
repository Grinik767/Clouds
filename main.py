import click

from cloud_boss import CloudBoss


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = CloudBoss()


@cli.command()
@click.option('--cloud', type=click.Choice(['yandex', 'dropbox'], case_sensitive=False),
              prompt='Выберите облако (Yandex/Dropbox)', help='Выбор облака')
@click.pass_context
def info(ctx, cloud: str):
    """Получить информацию об облаке."""
    ctx.obj.get_cloud_info(cloud)


@cli.command()
@click.argument('path', default="/")
@click.option('--cloud', type=click.Choice(['yandex', 'dropbox'], case_sensitive=False),
              prompt='Выберите облако (Yandex/Dropbox)', help='Выбор облака')
@click.pass_context
def folder_content(ctx, path: str, cloud: str):
    """Получить содержимое папки в облаке."""
    ctx.obj.get_folder_content(cloud, path)


@cli.command()
@click.argument('path')
@click.option('--cloud', type=click.Choice(['yandex', 'dropbox'], case_sensitive=False),
              prompt='Выберите облако (Yandex/Dropbox)', help='Выбор облака')
@click.pass_context
def create_folder(ctx, path: str, cloud: str):
    """Создать папку в облаке."""
    ctx.obj.create_folder(cloud, path)

@cli.command()
@click.option('--cloud', type=click.Choice(['yandex', 'dropbox'], case_sensitive=False),
              prompt='Выберите облако (Yandex/Dropbox)', help='Выбор облака')
@click.argument('path_remote')
@click.argument('path_local')
@click.pass_context
def download(ctx, path_remote: str, path_local: str, cloud: str):
    """Скачать файл/папку из облака."""
    ctx.obj.download(cloud, path_remote, path_local)


@cli.command()
@click.option('--cloud', type=click.Choice(['yandex', 'dropbox'], case_sensitive=False),
              prompt='Выберите облако (Yandex/Dropbox)', help='Выбор облака')
@click.argument('path_local')
@click.argument('path_remote')
@click.pass_context
def upload(ctx, path_local: str, path_remote: str, cloud: str):
    """Загрузить файл/папку в облако."""
    ctx.obj.upload(cloud, path_local, path_remote)


if __name__ == '__main__':
    cli()
