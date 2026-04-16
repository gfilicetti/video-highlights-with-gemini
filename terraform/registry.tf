resource "google_artifact_registry_repository" "video_repo" {
  location      = var.region
  repository_id = "video-highlights-repo"
  description   = "Docker repository for Video Highlights services"
  format        = "DOCKER"
}
