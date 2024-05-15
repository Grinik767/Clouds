from cloud_boss import CloudBoss
import click


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
        ctx.obj.get_cloud_info(cloud)
    else:
        pass


if __name__ == '__main__':
    cli()
