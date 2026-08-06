"""MinIO (S3-compatible) storage adapter.

STUB — the ``minio`` Python package is not installed. To use:
    pip install minio

Calls: minio.Minio client (put_object, fget_object, list_objects)
"""

from __future__ import annotations

from typing import Any

from adapters import StorageAdapter


class MinIOAdapter(StorageAdapter):
    """Object storage via MinIO (S3-compatible).

    Configure endpoint, access/secret keys, and bucket at init time.
    This is a stub — the real implementation uses ``minio.Minio``.
    """

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        bucket: str = "shunya",
        secure: bool = False,
    ) -> None:
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.secure = secure

    def upload(self, local_path: str, remote_path: str) -> bool:
        """Upload *local_path* to *remote_path* in the configured bucket."""
        # Real:
        #   from minio import Minio
        #   client = Minio(self.endpoint, self.access_key, self.secret_key,
        #                  secure=self.secure)
        #   if not client.bucket_exists(self.bucket):
        #       client.make_bucket(self.bucket)
        #   client.fput_object(self.bucket, remote_path, local_path)
        #   return True
        print(
            f"[stub] MinIOAdapter.upload('{local_path}', '{remote_path}') "
            f"→ bucket={self.bucket} @ {self.endpoint}"
        )
        return True

    def download(self, remote_path: str, local_path: str) -> bool:
        """Download *remote_path* from the configured bucket to *local_path*."""
        # Real:
        #   from minio import Minio
        #   client = Minio(self.endpoint, self.access_key, self.secret_key,
        #                  secure=self.secure)
        #   client.fget_object(self.bucket, remote_path, local_path)
        #   return True
        print(
            f"[stub] MinIOAdapter.download('{remote_path}', '{local_path}') "
            f"← bucket={self.bucket} @ {self.endpoint}"
        )
        return True

    def list(self, prefix: str = "") -> list[str]:
        """List objects under *prefix* in the configured bucket."""
        # Real:
        #   from minio import Minio
        #   client = Minio(self.endpoint, self.access_key, self.secret_key,
        #                  secure=self.secure)
        #   return [obj.object_name
        #           for obj in client.list_objects(self.bucket, prefix=prefix)]
        print(
            f"[stub] MinIOAdapter.list('{prefix}') "
            f"← bucket={self.bucket} @ {self.endpoint}"
        )
        return [f"{prefix}stub-object-1.txt", f"{prefix}stub-object-2.txt"]