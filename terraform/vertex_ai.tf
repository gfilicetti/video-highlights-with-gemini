resource "google_vertex_ai_index" "video_transcript_index" {
  provider     = google-beta
  display_name = "video-transcript-index"
  description  = "Index for video transcript chunks"
  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.video_bucket.name}/vector_search_index/"
    config {
      dimensions                  = 768
      approximate_neighbors_count = 150
      distance_measure_type       = "DOT_PRODUCT_DISTANCE"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 500
          leaf_nodes_to_search_percent = 7
        }
      }
    }
  }
  index_update_method = "STREAM_UPDATE"
}

resource "google_vertex_ai_index_endpoint" "video_transcript_endpoint" {
  provider     = google-beta
  display_name = "video-transcript-endpoint"
  public_endpoint_enabled = true
}

resource "google_vertex_ai_index_endpoint_deployed_index" "deployed_index" {
  provider           = google-beta
  index_endpoint     = google_vertex_ai_index_endpoint.video_transcript_endpoint.id
  deployed_index_id  = "video_transcript_deployed_index"
  index              = google_vertex_ai_index.video_transcript_index.id
  
  # Optional: but recommended for production
  dedicated_resources {
    machine_spec {
      machine_type = "n1-standard-2"
    }
    min_replica_count = 1
    max_replica_count = 1
  }
}
