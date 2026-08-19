import json
from pathlib import Path
from typing import Any


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
