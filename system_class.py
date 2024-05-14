import os
from dotenv import load_dotenv


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
        raise Exception(".env файл не смог быть подгружен")
