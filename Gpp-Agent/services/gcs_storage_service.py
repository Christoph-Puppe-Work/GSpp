import os
import json
from google.cloud import storage

class GcsStorageService:
    def __init__(self, bucket_name: str | None = None):
        self.bucket_name = bucket_name or os.environ.get("GCS_BUCKET_NAME")
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)

    def _get_path(self, iv_id: str, save_id: str, filename: str) -> str:
        return f"{iv_id}/saves/{save_id}/{filename}"

    async def save_json(self, iv_id: str, save_id: str, filename: str, data: dict):
        path = self._get_path(iv_id, save_id, filename)
        blob = self.bucket.blob(path)
        blob.upload_from_string(json.dumps(data, indent=2), content_type="application/json")
        return path

    async def load_json(self, iv_id: str, save_id: str, filename: str) -> dict:
        path = self._get_path(iv_id, save_id, filename)
        blob = self.bucket.blob(path)
        content = blob.download_as_text()
        return json.loads(content)

    async def list_saves(self, iv_id: str) -> list[str]:
        prefix = f"{iv_id}/saves/"
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix, delimiter='/')
        # This is a simplification; listing prefixes in GCS can be more involved
        saves = set()
        for blob in blobs:
            parts = blob.name[len(prefix):].split('/')
            if parts:
                saves.add(parts[0])
        return sorted(list(saves))
