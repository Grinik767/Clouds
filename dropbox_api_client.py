import json

import httpx
from os import path, getenv
from system_class import SystemClass
from api_client import Cloud


class Dropbox(Cloud):
    def __init__(self, auth_token: str) -> None:
        self.session = None
        self.url = "https://api.dropboxapi.com/2/"
        self.auth(auth_token)
        self.auth_token = auth_token

    def auth(self, auth_token: str) -> None:
        r = httpx.post(f"{self.url}users/get_current_account", headers={"Authorization": f"Bearer {auth_token}"})
        if r.status_code == httpx.codes.OK:
            self.session = httpx.Client()
            self.session.headers = {"Authorization": auth_token}
            return
        self.error_worker(
            {"error": {".tag": "AuthError"}, "error_summary": "Ошибка авторизации в Dropbox. Проверьте/обновите данные"})

    def get_cloud_info(self) -> dict:
        r = self.session.post(f"{self.url}users/get_space_usage",
                              headers={"Authorization": f"Bearer {self.auth_token}"})
        if r.status_code != httpx.codes.OK:
            return self.error_worker(r.json())
        used_space = r.json()["used"]
        r = httpx.post(f"{self.url}users/get_current_account", headers={"Authorization": f"Bearer {self.auth_token}"})
        if r.status_code != httpx.codes.OK:
            return self.error_worker(r.json())
        usage_info = r.json()
        return {
            "name": usage_info["name"]["display_name"],
            "email": usage_info["email"],
            "used_space": used_space / 2 ** 20,
            "total_space": ""
        }

    def get_folder_content(self, path: str) -> dict:
        headers = {"Authorization": f"Bearer {self.auth_token}",
                   "Content-Type": "application/json"}
        r = self.session.post(f"{self.url}files/get_metadata", headers=headers,
                              json={"include_deleted": False, "include_has_explicit_shared_members": False,
                                    "include_media_info": False, "path": path
                                    })
        if r.status_code != httpx.codes.OK:
            return self.error_worker(r.json())
        if r.json()['.tag'] != "folder":
            return self.error_worker(
                {"error": {".tag": "NotAFolder"}, "error_summary": "Запрошенный ресурс не является папкой"})

        r = self.session.post(f"{self.url}files/list_folder",
                              json={"path": path, "recursive": False, "include_media_info": False,
                                    "include_deleted": False, "include_has_explicit_shared_members": False
                                    }, headers=headers)
        if r.status_code != httpx.codes.OK:
            return self.error_worker(r.json())

        content_info = r.json()
        files = [entry["name"] for entry in content_info["entries"] if
                 isinstance(entry, dict) and entry[".tag"] == "file"]
        folders = [entry["name"] for entry in content_info["entries"] if
                   isinstance(entry, dict) and entry[".tag"] == "folder"]
        return {"folders": folders, "files": files}

    def download_file(self, path_remote: str, path_local: str) -> dict:
        dropbox_api_arg = json.dumps({"path": path_remote})

        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Dropbox-API-Arg": dropbox_api_arg
        }
        r = self.session.post(f"https://content.dropboxapi.com/2/files/download", headers=headers)
        if r.status_code != 200:
            return self.error_worker(r.json())
        try:
            with open(path.abspath(path_local), 'wb') as file:
                print(r.content)
                file.write(r.content)
            return {"status": "ok"}
        except FileNotFoundError:
            return self.error_worker({
                "error": {".tag": "FileNotFoundError"},
                "error_summary": f"Неверный путь: {path.abspath(path_local)}"
            })

    def upload_file(self, path_local: str, path_remote: str) -> dict:
        data = {
            "path": path_remote,
            "mode": "add",
            "autorename": True,
            "mute": False
        }
        try:
            with open(path_local, "rb") as f:
                files = {"file": f}
                headers = {
                    "Authorization": f"Bearer {self.auth_token}",
                    "Dropbox-API-Arg": json.dumps(data),
                    "Content-Type": "application/octet-stream"
                }
                r = self.session.post("https://content.dropboxapi.com/2/files/upload", headers=headers, files=files)
                if r.status_code != 200:
                    return self.error_worker(r.json())
        except FileNotFoundError:
            return self.error_worker({
                "error": {".tag": "FileNotFoundError"},
                "error_summary": f"Файл не найден: {path_local}"
            })

        if r.status_code == 200:
            return {"status": "ok"}
        else:
            return self.error_worker(r.json())

    def create_folder(self, path: str) -> dict:
        data = {"path": path, "autorename": False}
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        r = self.session.post("https://api.dropboxapi.com/2/files/create_folder_v2", json=data, headers=headers)
        print(r.status_code)
        if r.status_code == 200:
            return {"status": "ok"}
        else:
            return self.error_worker(r.json())

    @staticmethod
    def error_worker(response: dict):
        with SystemClass.except_handler(SystemClass.exchandler):
            raise Exception(f"{response['error']['.tag']}. {response['error_summary']}")


if __name__ == '__main__':
    driver = Dropbox("")