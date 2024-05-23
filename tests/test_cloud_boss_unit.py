from unittest.mock import patch

import pytest
from click.testing import CliRunner

from main import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cloud_boss_mock():
    with patch('main.CloudBoss') as MockClass:
        yield MockClass.return_value


def test_info_command(runner, cloud_boss_mock):
    result = runner.invoke(cli, ['info', '--cloud', 'yandex'])
    assert result.exit_code == 0
    cloud_boss_mock.get_cloud_info.assert_called_once_with('yandex')


def test_folder_content_command(runner, cloud_boss_mock):
    result = runner.invoke(cli, ['folder-content', '/', '--cloud', 'yandex'])
    assert result.exit_code == 0
    cloud_boss_mock.get_folder_content.assert_called_once_with('yandex', '/')


def test_create_folder_command(runner, cloud_boss_mock):
    result = runner.invoke(cli, ['create-folder', 'new_folder', '--cloud', 'yandex'])
    assert result.exit_code == 0
    cloud_boss_mock.create_folder.assert_called_once_with('yandex', 'new_folder')


def test_download_command(runner, cloud_boss_mock):
    result = runner.invoke(cli, ['download', 'remote_path', 'local_path', '--cloud', 'yandex'])
    assert result.exit_code == 0
    cloud_boss_mock.download.assert_called_once_with('yandex', 'remote_path', 'local_path')


def test_upload_command(runner, cloud_boss_mock):
    result = runner.invoke(cli, ['upload', 'local_path', 'remote_path', '--cloud', 'yandex'])
    assert result.exit_code == 0
    cloud_boss_mock.upload.assert_called_once_with('yandex', 'local_path', 'remote_path')
