variable "project_id" {
  description = "Google Cloud project ID that owns the MarketPulse resources."
  type        = string
}

variable "raw_bucket_name" {
  description = "Globally unique Cloud Storage bucket for immutable raw API payloads."
  type        = string
}

variable "raw_bucket_location" {
  description = "Regional location of the raw Cloud Storage bucket."
  type        = string
  default     = "US-CENTRAL1"
}

variable "bigquery_dataset_id" {
  description = "BigQuery dataset containing curated and analytical tables."
  type        = string
}

variable "bigquery_location" {
  description = "Location of the BigQuery dataset."
  type        = string
  default     = "US"
}

variable "bigquery_table_id" {
  description = "BigQuery table containing curated daily prices."
  type        = string
  default     = "daily_prices"
}
