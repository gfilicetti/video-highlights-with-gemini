resource "google_project_service" "eventarc" {
  service            = "eventarc.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "videointelligence" {
  service            = "videointelligence.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "aiplatform" {
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifactregistry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}
