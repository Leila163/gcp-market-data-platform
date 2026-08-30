resource "google_storage_bucket" "raw" {
  name                        = var.raw_bucket_name
  project                     = var.project_id
  location                    = var.raw_bucket_location
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  soft_delete_policy {
    retention_duration_seconds = 0
  }

  lifecycle {
    prevent_destroy = true
  }
}
