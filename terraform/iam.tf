# Backend Service Account
resource "google_service_account" "backend_sa" {
  account_id   = "video-highlights-backend-sa"
  display_name = "Video Highlights Backend Service Account"
}

# Frontend Service Account
resource "google_service_account" "frontend_sa" {
  account_id   = "video-highlights-frontend-sa"
  display_name = "Video Highlights Frontend Service Account"
}

# Permissions for Backend
resource "google_project_iam_member" "backend_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_bq_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_bq_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_storage_user" {
  project = var.project_id
  role    = "roles/storage.objectUser"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_video_intelligence" {
  project = var.project_id
  role    = "roles/videointelligence.serviceAgent"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

# Permissions for Frontend
resource "google_project_iam_member" "frontend_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.frontend_sa.email}"
}

resource "google_project_iam_member" "frontend_bq_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.frontend_sa.email}"
}

resource "google_project_iam_member" "frontend_bq_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.frontend_sa.email}"
}

resource "google_project_iam_member" "frontend_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.frontend_sa.email}"
}

resource "google_project_iam_member" "frontend_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.frontend_sa.email}"
}
