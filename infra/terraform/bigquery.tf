resource "google_bigquery_dataset" "analytics" {
  project                    = var.project_id
  dataset_id                 = var.bigquery_dataset_id
  location                   = var.bigquery_location
  description                = "Curated and analytical US equity market data for MarketPulse."
  delete_contents_on_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_bigquery_table" "daily_prices" {
  project             = var.project_id
  dataset_id          = google_bigquery_dataset.analytics.dataset_id
  table_id            = var.bigquery_table_id
  description         = "Curated daily OHLCV prices for US equities."
  deletion_protection = true
  schema              = file("${path.module}/../../schemas/daily_prices.json")

  time_partitioning {
    type  = "DAY"
    field = "trading_date"
  }

  clustering = ["symbol"]

  lifecycle {
    prevent_destroy = true
  }
}
