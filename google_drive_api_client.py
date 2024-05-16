from api_client import Cloud
from system_class import SystemClass
from os import path, getenv
import httpx


class GoogleDrive(Cloud):
    def __init__(self, auth_token: str) -> None:
        self.session = None
        self.url = "https://www.googleapis.com/drive/v3/"
        self.auth(auth_token)
        self.token = auth_token

    def auth(self, auth_token: str) -> None:
        self.session = httpx.Client(headers={"Authorization": f"Bearer {auth_token}"})

    def get_cloud_info(self) -> dict:
        with self.session:
            r = self.session.get(f"{self.url}about", params={"fields": "user,storageQuota"})
        if r.status_code != 200:
            return self.error_worker(r.json())
        answer = r.json()
        return {
            "login": answer["user"]["emailAddress"],
            "name": answer["user"]["displayName"],
            "total_space": int(answer["storageQuota"]["limit"]) / (2 ** 20),
            "used_space": int(answer["storageQuota"]["usage"]) / (2 ** 20)
        }

    import httpx

    def get_folder_content(self, folder_id: str) -> dict:
        params = {
            "q": f"name = '{folder_id}' and mimeType = 'application/vnd.google-apps.folder'",
            "fields": "files(id)"
        }
        r = self.session.get(f"{self.url}files", params=params)
        if r.status_code != 200:
            return self.error_worker(r.json())

        folder_data = r.json().get("files", [])
        if not folder_data:
            return self.error_worker({"error": "DiskNotFoundError", "message": "Не удалось найти запрошенный ресурс или он не является папкой."})

        folder_id = folder_data[0]["id"]

        params = {
            "q": f"'{folder_id}' in parents",
            "fields": "files(id, name, mimeType)"
        }
        r = self.session.get(f"{self.url}files", params=params)
        if r.status_code != 200:
            return self.error_worker(r.json())

        files, folders = [], []
        for item in r.json().get('files', []):
            if item["mimeType"] == "application/vnd.google-apps.folder":
                folders.append(item["name"])
            else:
                files.append(item["name"])
        return {"folders": folders, "files": files}

    def download_file(self, file_id: str, path_local: str) -> dict:
        with self.session:
            r = self.session.get(f"{self.url}files/{file_id}", params={"alt": "media"})
            if r.status_code != 200:
                return self.error_worker(r.json())
        try:
            with open(path.abspath(path_local), 'wb') as file:
                file.write(r.content)
            return {"status": "ok"}
        except FileNotFoundError:
            return self.error_worker(
                {"error": "FileNotFoundError", "message": f"Invalid path: {path.abspath(path_local)}"}
            )

    def get_folder_id(self, folder_name) :
        params = {
            "q": f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'",
            "fields": "files(id)"
        }
        r = self.session.get(f"{self.url}files", params=params)
        if r.status_code != 200:
            return self.error_worker(r.json())

        folder_data = r.json().get("files", [])
        if not folder_data:
            return self.error_worker({"error": "DiskNotFoundError",
                                      "message": "Не удалось найти запрошенный ресурс или он не является папкой."})

    def upload_file(self, path_local: str, folder_id: str) -> dict:
        if not path.isfile(path_local):
            return self.error_worker({"error": "NotAFile", "message": "Загружаемый ресурс не является файлом"})

        with open(path.abspath(path_local), 'rb') as data:
            headers = {"Content-Type": "application/octet-stream"}
            params = {
                "uploadType": "media",
                "name": path.basename(path_local),
                "parents": ["1JqdHyCh13Ncsls7laFYCir-djkcSncbh"],
            }
            with self.session:
                r = self.session.post(f"https://www.googleapis.com/upload/drive/v3/files", headers=headers,
                                      params=params, data=data)
        if r.status_code == 200:
            return {"status": "ok"}
        return self.error_worker(r.json())

    def create_folder(self, folder_name: str, parent_id: str = None) -> dict:
        metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [parent_id]
        with self.session:
            r = self.session.post(f"{self.url}files", json=metadata)
        if r.status_code == 200:
            return {"status": "ok"}
        return self.error_worker(r.json())

    # just for unit tests
    def delete_folder(self, folder_id: str) -> None:
        httpx.delete(f"{self.url}files/{folder_id}", headers={"Authorization": f"Bearer {getenv('DEV_AUTH_TOKEN_GOOGLE')}"})

    @staticmethod
    def error_worker(response: dict):
        with SystemClass.except_handler(SystemClass.exchandler):
            raise Exception(f"{response['error']}. {response['message']}")


if __name__ == '__main__':
    pass