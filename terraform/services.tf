resource "google_cloud_run_v2_service" "backend" {
  name     = "video-highlights-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend_sa.email
    containers {
      image = var.backend_image
      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GCP_LOCATION"
        value = var.region
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = var.bigquery_dataset_id
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.video_bucket.name
      }
      env {
        name  = "VECTOR_SEARCH_INDEX_ENDPOINT"
        value = google_vertex_ai_index_endpoint.video_transcript_endpoint.id
      }
      env {
        name  = "VECTOR_SEARCH_INDEX_ID"
        value = google_vertex_ai_index.video_transcript_index.id
      }
      env {
        name  = "VECTOR_SEARCH_DEPLOYED_INDEX_ID"
        value = "video_transcript_deployed_index"
      }
    }
  }
}

resource "google_cloud_run_v2_service" "frontend" {
  name     = "video-highlights-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.frontend_sa.email
    containers {
      image = var.frontend_image
      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GCP_LOCATION"
        value = var.region
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = var.bigquery_dataset_id
      }
      env {
        name  = "VECTOR_SEARCH_INDEX_ENDPOINT"
        value = google_vertex_ai_index_endpoint.video_transcript_endpoint.id
      }
      env {
        name  = "VECTOR_SEARCH_INDEX_ID"
        value = google_vertex_ai_index.video_transcript_index.id
      }
      env {
        name  = "VECTOR_SEARCH_DEPLOYED_INDEX_ID"
        value = "video_transcript_deployed_index"
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "frontend_unauthenticated" {
  location = google_cloud_run_v2_service.frontend.location
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
