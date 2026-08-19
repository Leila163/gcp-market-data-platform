import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from marketpulse.models import DailyPrice


def write_raw_payload(
    *,
    payload: dict[str, Any],
    destination: Path,
) -> None:
    """Write a raw API payload without overwriting existing data."""
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with destination.open(
        mode="x",
        encoding="utf-8",
        newline="\n",
    ) as output_file:
        json.dump(
            payload,
            output_file,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        output_file.write("\n")


def write_daily_prices_jsonl(
    *,
    records: Sequence[DailyPrice],
    destination: Path,
) -> int:
    """Write validated daily prices as newline-delimited JSON."""
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with destination.open(
        mode="w",
        encoding="utf-8",
        newline="\n",
    ) as output_file:
        for record in records:
            json.dump(
                record.model_dump(mode="json"),
                output_file,
                ensure_ascii=False,
                sort_keys=True,
            )
            output_file.write("\n")

    return len(records)
