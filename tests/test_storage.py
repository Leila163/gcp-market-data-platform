import json

import pytest

from marketpulse.storage import write_raw_payload


def test_write_raw_payload_creates_parent_directories(tmp_path) -> None:
    destination = tmp_path / "raw" / "alpha_vantage" / "LRCX" / "2026-08-18.json"
    payload = {
        "Meta Data": {
            "2. Symbol": "LRCX",
        },
        "Time Series (Daily)": {},
    }

    write_raw_payload(
        payload=payload,
        destination=destination,
    )

    assert destination.exists()
    assert json.loads(destination.read_text(encoding="utf-8")) == payload


def test_write_raw_payload_refuses_to_overwrite_existing_file(
    tmp_path,
) -> None:
    destination = tmp_path / "raw" / "LRCX.json"
    original_payload = {"version": "original"}

    write_raw_payload(
        payload=original_payload,
        destination=destination,
    )

    with pytest.raises(FileExistsError):
        write_raw_payload(
            payload={"version": "replacement"},
            destination=destination,
        )

    assert json.loads(destination.read_text(encoding="utf-8")) == (original_payload)
