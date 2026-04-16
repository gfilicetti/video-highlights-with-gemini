output "video_bucket_name" {
  value = google_storage_bucket.video_bucket.name
}

output "bigquery_dataset_id" {
  value = google_bigquery_dataset.video_metadata.dataset_id
}

output "backend_url" {
  value = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  value = google_cloud_run_v2_service.frontend.uri
}

output "artifact_registry_repo" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.video_repo.name}"
}

output "vector_search_index_id" {
  value = google_vertex_ai_index.video_transcript_index.id
}

output "vector_search_endpoint_id" {
  value = google_vertex_ai_index_endpoint.video_transcript_endpoint.id
}
