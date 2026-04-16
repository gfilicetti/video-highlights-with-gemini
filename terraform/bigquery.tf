resource "google_bigquery_dataset" "video_metadata" {
  dataset_id = var.bigquery_dataset_id
  location   = var.region
}

resource "google_bigquery_table" "video_chapters" {
  dataset_id = google_bigquery_dataset.video_metadata.dataset_id
  table_id   = "video_chapters"
  deletion_protection = false

  schema = <<EOF
[
  {"name": "source_video_uri", "type": "STRING", "mode": "NULLABLE"},
  {"name": "chapter_number", "type": "INT64", "mode": "NULLABLE"},
  {"name": "title", "type": "STRING", "mode": "NULLABLE"},
  {"name": "summary", "type": "STRING", "mode": "NULLABLE"},
  {"name": "start_time_seconds", "type": "FLOAT64", "mode": "NULLABLE"},
  {"name": "end_time_seconds", "type": "FLOAT64", "mode": "NULLABLE"}
]
EOF
}

resource "google_bigquery_table" "video_chunks" {
  dataset_id = google_bigquery_dataset.video_metadata.dataset_id
  table_id   = "video_chunks"
  deletion_protection = false

  schema = <<EOF
[
  {"name": "chunk_id", "type": "STRING", "mode": "NULLABLE"},
  {"name": "source_video_uri", "type": "STRING", "mode": "NULLABLE"},
  {"name": "chapter_number", "type": "INT64", "mode": "NULLABLE"},
  {"name": "chunk_number", "type": "INT64", "mode": "NULLABLE"},
  {"name": "chunk_text", "type": "STRING", "mode": "NULLABLE"}
]
EOF
}

resource "google_bigquery_table" "video_transcript_words" {
  dataset_id = google_bigquery_dataset.video_metadata.dataset_id
  table_id   = "video_transcript_words"
  deletion_protection = false

  schema = <<EOF
[
  {"name": "source_video_uri", "type": "STRING", "mode": "NULLABLE"},
  {"name": "word", "type": "STRING", "mode": "NULLABLE"},
  {"name": "start_time_seconds", "type": "FLOAT64", "mode": "NULLABLE"},
  {"name": "end_time_seconds", "type": "FLOAT64", "mode": "NULLABLE"}
]
EOF
}

resource "google_bigquery_table" "scene_embeddings" {
  dataset_id = google_bigquery_dataset.video_metadata.dataset_id
  table_id   = "scene_embeddings"
  deletion_protection = false

  schema = <<EOF
[
  {"name": "source_video_uri", "type": "STRING", "mode": "NULLABLE"},
  {"name": "moment_id", "type": "STRING", "mode": "NULLABLE"},
  {"name": "label", "type": "STRING", "mode": "NULLABLE"},
  {"name": "reason", "type": "STRING", "mode": "NULLABLE"},
  {"name": "start_time", "type": "FLOAT64", "mode": "NULLABLE"},
  {"name": "end_time", "type": "FLOAT64", "mode": "NULLABLE"},
  {"name": "embedding", "type": "FLOAT64", "mode": "REPEATED"}
]
EOF
}
