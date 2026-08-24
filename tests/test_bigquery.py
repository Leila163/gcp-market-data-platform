from pathlib import Path
from unittest.mock import Mock

import pytest
from google.cloud import bigquery

from marketpulse.bigquery import (
    BigQueryDailyPriceLoader,
    build_daily_prices_load_config,
    build_daily_prices_merge_sql,
)


def test_build_daily_prices_load_config_uses_strict_json_schema() -> None:
    config = build_daily_prices_load_config()

    assert config.source_format == bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    assert config.write_disposition == bigquery.WriteDisposition.WRITE_TRUNCATE
    assert config.autodetect is False
    assert config.ignore_unknown_values is False
    assert config.max_bad_records == 0

    assert [(field.name, field.field_type, field.mode) for field in config.schema] == [
        ("symbol", "STRING", "REQUIRED"),
        ("trading_date", "DATE", "REQUIRED"),
        ("open", "NUMERIC", "REQUIRED"),
        ("high", "NUMERIC", "REQUIRED"),
        ("low", "NUMERIC", "REQUIRED"),
        ("close", "NUMERIC", "REQUIRED"),
        ("volume", "INTEGER", "REQUIRED"),
        ("source", "STRING", "REQUIRED"),
    ]


def test_build_daily_prices_merge_sql_uses_business_key_and_upsert() -> None:
    sql = build_daily_prices_merge_sql(
        target_table="test-project.marketpulse_analytics.daily_prices",
        staging_table="test-project.marketpulse_analytics.daily_prices_staging",
    )

    assert "MERGE `test-project.marketpulse_analytics.daily_prices` AS target" in sql
    assert "USING `test-project.marketpulse_analytics.daily_prices_staging` AS source" in sql

    assert "target.symbol = source.symbol" in sql
    assert "target.trading_date = source.trading_date" in sql
    assert "target.source = source.source" in sql

    assert "WHEN MATCHED AND" in sql
    assert "target.close IS DISTINCT FROM source.close" in sql
    assert "THEN UPDATE SET" in sql

    assert "WHEN NOT MATCHED THEN" in sql
    assert "INSERT" in sql
    assert "VALUES" in sql


def test_upsert_jsonl_stages_merges_and_cleans_up(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "daily_prices.jsonl"
    source_path.write_text(
        '{"symbol":"LRCX"}\n',
        encoding="utf-8",
    )

    load_job = Mock()
    load_job.output_rows = 1

    merge_job = Mock()
    merge_job.num_dml_affected_rows = 1

    client = Mock()
    client.load_table_from_file.return_value = load_job
    client.query.return_value = merge_job

    loader = BigQueryDailyPriceLoader(
        client=client,
        project_id="test-project",
        dataset_id="marketpulse_analytics",
        table_id="daily_prices",
        location="US",
    )

    result = loader.upsert_jsonl(
        source_path=source_path,
    )

    load_call = client.load_table_from_file.call_args
    staging_table = load_call.args[1]

    assert staging_table.startswith("test-project.marketpulse_analytics.daily_prices_staging_")
    assert load_call.kwargs["location"] == "US"
    assert isinstance(
        load_call.kwargs["job_config"],
        bigquery.LoadJobConfig,
    )
    load_job.result.assert_called_once_with()

    query_call = client.query.call_args
    merge_sql = query_call.args[0]

    assert "MERGE `test-project.marketpulse_analytics.daily_prices`" in merge_sql
    assert f"USING `{staging_table}`" in merge_sql
    assert query_call.kwargs["location"] == "US"
    assert query_call.kwargs["job_config"].maximum_bytes_billed == 10_485_760
    merge_job.result.assert_called_once_with()

    client.delete_table.assert_called_once_with(
        staging_table,
        not_found_ok=True,
    )

    assert result.target_table == ("test-project.marketpulse_analytics.daily_prices")
    assert result.input_rows == 1
    assert result.affected_rows == 1


def test_upsert_jsonl_cleans_up_when_merge_fails(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "daily_prices.jsonl"
    source_path.write_text(
        '{"symbol":"LRCX"}\n',
        encoding="utf-8",
    )

    load_job = Mock()
    load_job.output_rows = 1

    merge_job = Mock()
    merge_job.result.side_effect = RuntimeError("merge failed")

    client = Mock()
    client.load_table_from_file.return_value = load_job
    client.query.return_value = merge_job

    loader = BigQueryDailyPriceLoader(
        client=client,
        project_id="test-project",
        dataset_id="marketpulse_analytics",
        table_id="daily_prices",
        location="US",
    )

    with pytest.raises(
        RuntimeError,
        match="merge failed",
    ):
        loader.upsert_jsonl(
            source_path=source_path,
        )

    staging_table = client.load_table_from_file.call_args.args[1]

    client.delete_table.assert_called_once_with(
        staging_table,
        not_found_ok=True,
    )
