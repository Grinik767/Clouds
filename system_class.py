import os
import sys
from contextlib import contextmanager
from logging import getLogger
from typing import Callable

from dotenv import load_dotenv

logger = getLogger(__name__)


class SystemClass:
    @staticmethod
    def load_env(dev=True):
        if dev:
            env_name = ".env.dev"
        else:
            env_name = ".env.prod"
        dotenv_path = os.path.join(os.path.dirname(__file__), env_name)
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
            return
        with SystemClass.except_handler(SystemClass.exchandler):
            raise Exception(".env файл не смог быть подгружен")

    @contextmanager
    def except_handler(self: Callable):
        sys.excepthook = self
        yield
        sys.excepthook = sys.__excepthook__

    @staticmethod
    def exchandler(type, value, traceback):
        logger.error(value)
