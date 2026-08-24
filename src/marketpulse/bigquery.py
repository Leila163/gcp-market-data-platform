from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from google.cloud import bigquery

DAILY_PRICE_SCHEMA = [
    bigquery.SchemaField(
        "symbol",
        "STRING",
        mode="REQUIRED",
    ),
    bigquery.SchemaField(
        "trading_date",
        "DATE",
        mode="REQUIRED",
    ),
    bigquery.SchemaField(
        "open",
        "NUMERIC",
        mode="REQUIRED",
    ),
    bigquery.SchemaField(
        "high",
        "NUMERIC",
        mode="REQUIRED",
    ),
    bigquery.SchemaField(
        "low",
        "NUMERIC",
        mode="REQUIRED",
    ),
    bigquery.SchemaField(
        "close",
        "NUMERIC",
        mode="REQUIRED",
    ),
    bigquery.SchemaField(
        "volume",
        "INTEGER",
        mode="REQUIRED",
    ),
    bigquery.SchemaField(
        "source",
        "STRING",
        mode="REQUIRED",
    ),
]


def build_daily_prices_load_config() -> bigquery.LoadJobConfig:
    """Build a strict JSONL load configuration for a staging table."""
    return bigquery.LoadJobConfig(
        schema=DAILY_PRICE_SCHEMA,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=False,
        ignore_unknown_values=False,
        max_bad_records=0,
    )


def build_daily_prices_merge_sql(
    *,
    target_table: str,
    staging_table: str,
) -> str:
    """Build an idempotent BigQuery upsert for daily price records."""
    return f"""
MERGE `{target_table}` AS target
USING `{staging_table}` AS source
ON target.symbol = source.symbol
AND target.trading_date = source.trading_date
AND target.source = source.source
WHEN MATCHED AND (
    target.open IS DISTINCT FROM source.open
    OR target.high IS DISTINCT FROM source.high
    OR target.low IS DISTINCT FROM source.low
    OR target.close IS DISTINCT FROM source.close
    OR target.volume IS DISTINCT FROM source.volume
) THEN UPDATE SET
    open = source.open,
    high = source.high,
    low = source.low,
    close = source.close,
    volume = source.volume
WHEN NOT MATCHED THEN
    INSERT (
        symbol,
        trading_date,
        open,
        high,
        low,
        close,
        volume,
        source
    )
    VALUES (
        source.symbol,
        source.trading_date,
        source.open,
        source.high,
        source.low,
        source.close,
        source.volume,
        source.source
    )
""".strip()


@dataclass(frozen=True)
class BigQueryUpsertResult:
    """Summary of one completed BigQuery upsert."""

    target_table: str
    input_rows: int
    affected_rows: int


class BigQueryDailyPriceLoader:
    """Load curated daily prices through a staging table and MERGE."""

    def __init__(
        self,
        *,
        client: bigquery.Client,
        project_id: str,
        dataset_id: str,
        table_id: str,
        location: str,
        maximum_bytes_billed: int = 10_485_760,
    ) -> None:
        self._client = client
        self._project_id = project_id
        self._dataset_id = dataset_id
        self._table_id = table_id
        self._location = location
        self._maximum_bytes_billed = maximum_bytes_billed

    @property
    def target_table(self) -> str:
        """Return the fully qualified destination table."""
        return f"{self._project_id}.{self._dataset_id}.{self._table_id}"

    def upsert_jsonl(
        self,
        *,
        source_path: Path,
    ) -> BigQueryUpsertResult:
        """Stage a JSONL file and merge it into the destination table."""
        file_digest = sha256(source_path.read_bytes()).hexdigest()[:16]

        staging_table = f"{self.target_table}_staging_{file_digest}"

        try:
            with source_path.open("rb") as source_file:
                load_job = self._client.load_table_from_file(
                    source_file,
                    staging_table,
                    job_config=build_daily_prices_load_config(),
                    location=self._location,
                )

            load_job.result()

            merge_job = self._client.query(
                build_daily_prices_merge_sql(
                    target_table=self.target_table,
                    staging_table=staging_table,
                ),
                job_config=bigquery.QueryJobConfig(
                    use_legacy_sql=False,
                    maximum_bytes_billed=self._maximum_bytes_billed,
                ),
                location=self._location,
            )
            merge_job.result()
        finally:
            self._client.delete_table(
                staging_table,
                not_found_ok=True,
            )

        return BigQueryUpsertResult(
            target_table=self.target_table,
            input_rows=int(load_job.output_rows or 0),
            affected_rows=int(merge_job.num_dml_affected_rows or 0),
        )
