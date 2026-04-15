resource "google_storage_bucket" "video_bucket" {
  name                        = var.gcs_bucket_name
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}
