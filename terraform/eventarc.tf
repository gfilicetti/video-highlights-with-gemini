# Get the project number
data "google_project" "project" {}

# Cloud Storage Service Agent
resource "google_project_iam_member" "gcs_pubsub_publishing" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com"
}

# Eventarc Trigger
resource "google_eventarc_trigger" "video_upload_trigger" {
  name     = "video-upload-trigger"
  location = var.region

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.video_bucket.name
  }

  destination {
    cloud_run_service {
      service = google_cloud_run_v2_service.backend.name
      region  = var.region
    }
  }

  service_account = google_service_account.backend_sa.email

  depends_on = [
    google_project_iam_member.backend_bq_editor,
    google_project_iam_member.gcs_pubsub_publishing
  ]
}
