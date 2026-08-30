output "raw_bucket_name" {
  description = "Name of the Cloud Storage raw-data bucket."
  value       = google_storage_bucket.raw.name
}

output "bigquery_dataset_id" {
  description = "ID of the MarketPulse BigQuery dataset."
  value       = google_bigquery_dataset.analytics.dataset_id
}

output "bigquery_table_id" {
  description = "ID of the curated daily-prices BigQuery table."
  value       = google_bigquery_table.daily_prices.table_id
}
