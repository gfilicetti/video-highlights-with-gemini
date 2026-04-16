variable "project_id" {
  description = "The GCP project ID to deploy to."
  type        = string
}

variable "region" {
  description = "The GCP region for resources."
  type        = string
  default     = "us-central1"
}

variable "gcs_bucket_name" {
  description = "The name of the GCS bucket for videos."
  type        = string
}

variable "bigquery_dataset_id" {
  description = "The ID of the BigQuery dataset."
  type        = string
  default     = "video_metadata_dataset"
}

variable "backend_image" {
  description = "The container image for the backend service."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "frontend_image" {
  description = "The container image for the frontend service."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}
