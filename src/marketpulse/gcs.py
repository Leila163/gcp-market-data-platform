from pathlib import Path

from google.api_core.exceptions import PreconditionFailed
from google.cloud import storage


class RawObjectAlreadyExistsError(RuntimeError):
    """Raised when a create-only raw upload targets an existing object."""


class GCSRawUploader:
    """Upload raw data files to a Google Cloud Storage bucket."""

    def __init__(
        self,
        *,
        bucket_name: str,
        client: storage.Client,
    ) -> None:
        self._bucket_name = bucket_name
        self._client = client

    def upload_raw_file(
        self,
        *,
        local_path: Path,
        object_name: str,
    ) -> str:
        """Upload a raw file without overwriting an existing cloud object."""
        storage_uri = f"gs://{self._bucket_name}/{object_name}"
        bucket = self._client.bucket(self._bucket_name)
        blob = bucket.blob(object_name)

        try:
            blob.upload_from_filename(
                str(local_path),
                content_type="application/json",
                if_generation_match=0,
                checksum="auto",
            )
        except PreconditionFailed as error:
            raise RawObjectAlreadyExistsError(
                f"Raw cloud object already exists: {storage_uri}"
            ) from error

        return storage_uri
