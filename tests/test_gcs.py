from unittest.mock import Mock

import pytest
from google.api_core.exceptions import PreconditionFailed
from google.cloud import storage

from marketpulse.gcs import (
    GCSRawUploader,
    RawObjectAlreadyExistsError,
)


def test_upload_raw_file_uses_create_only_precondition(tmp_path) -> None:
    local_path = tmp_path / "raw-response.json"
    local_path.write_text(
        '{"symbol": "LRCX"}\n',
        encoding="utf-8",
    )
    object_name = (
        "alpha_vantage/daily_prices/symbol=LRCX/ingestion_date=2026-08-20/20260820T120000Z.json"
    )

    client = Mock(spec=storage.Client)
    bucket = Mock()
    blob = Mock()

    client.bucket.return_value = bucket
    bucket.blob.return_value = blob

    uploader = GCSRawUploader(
        bucket_name="test-raw-bucket",
        client=client,
    )

    storage_uri = uploader.upload_raw_file(
        local_path=local_path,
        object_name=object_name,
    )

    client.bucket.assert_called_once_with("test-raw-bucket")
    bucket.blob.assert_called_once_with(object_name)
    blob.upload_from_filename.assert_called_once_with(
        str(local_path),
        content_type="application/json",
        if_generation_match=0,
        checksum="auto",
    )
    assert storage_uri == f"gs://test-raw-bucket/{object_name}"


def test_upload_raw_file_reports_existing_cloud_object(tmp_path) -> None:
    local_path = tmp_path / "raw-response.json"
    local_path.write_text(
        '{"symbol": "LRCX"}\n',
        encoding="utf-8",
    )
    object_name = "raw/existing-response.json"

    client = Mock(spec=storage.Client)
    blob = client.bucket.return_value.blob.return_value
    blob.upload_from_filename.side_effect = PreconditionFailed("Cloud object already exists.")

    uploader = GCSRawUploader(
        bucket_name="test-raw-bucket",
        client=client,
    )

    with pytest.raises(
        RawObjectAlreadyExistsError,
        match="gs://test-raw-bucket/raw/existing-response.json",
    ):
        uploader.upload_raw_file(
            local_path=local_path,
            object_name=object_name,
        )
