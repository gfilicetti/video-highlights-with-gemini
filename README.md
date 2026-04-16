# Video Highlighting with Gemini
This repo is a demo for various forms of AI enabled automatic highlighting and clipping using Gemini on GCP

## Architecture
The pipeline follows an event-driven, serverless architecture divided into a Backend Processing Engine and a Frontend Discovery UI.

1. **Ingestion (Eventarc):** A video uploaded to Google Cloud Storage (GCS) triggers the backend service.
2. **Backend Processing (Cloud Run):**
   * **Track A (Text/Dialogue):** Uses the Video Intelligence API to generate a precise, word-level transcript. Gemini formats this transcript into logical chapters. The text is chunked, embedded using Vertex AI Text Embeddings, and indexed in Vertex AI Vector Search.
   * **Track B (Visual/Action):** Gemini "watches" the video to identify highly memorable, high-impact moments. These specific video segments are embedded using Vertex AI Multimodal Embeddings (Video + Audio) and stored directly in BigQuery.
3. **Frontend UI (Streamlit on Cloud Run):**
   * **Memorable Moments Gallery:** Automatically curates and plays the multimodal visual highlights from BigQuery.
   * **Keyword Search & Directory:** Queries the Vertex AI Vector Search index to find specific quotes and displays a directory of all AI-generated chapters.

## Technology Used

* **Google Gemini (gemini-2.5-flash):** For logical reasoning, chapterization, and visual highlight identification.
* **Gemini Multimodal Embeddings (`gemini-embedding-2-preview`):** To generate vectors from raw video and audio streams.
* **Vertex AI Text Embeddings (`text-embedding-004`):** To generate vectors from transcript chunks.
* **Vertex AI Vector Search:** For sub-second semantic search across text passages.
* **Google Cloud Video Intelligence API:** For accurate speech-to-text transcription.
* **BigQuery:** For storing video metadata, chapters, and multimodal vectors.
* **Cloud Run & Eventarc:** For serverless backend execution and frontend hosting.
* **Streamlit:** For the interactive Python web UI.

## Initialization and Setup

### 0. Local Configuration
Before deploying or running locally, create a `.env` file from the template:
```bash
cp .env.template .env
```
Fill in the `.env` file with your GCP project details.

### Prerequisites
* A GCP Project with billing enabled.
* A GCS Bucket to host your videos (e.g., `gs://my-video-bucket`).
* A BigQuery Dataset (e.g., `video_metadata_dataset`).
* A deployed Vertex AI Vector Search Index.

### 1. Infrastructure Deployment (Terraform)
We use Terraform to deploy the entire stack.
1. Navigate to the `terraform/` directory.
2. Initialize Terraform:
   ```bash
   terraform init
   ```
3. Create a `terraform.tfvars` file from the example:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
   Edit `terraform.tfvars` with your specific values.
4. Plan and Apply:
   ```bash
   terraform plan
   terraform apply
   ```

### 2. BigQuery Setup (Manual Alternative)
Run the following SQL in your GCP Console to set up the required tables:
```sql
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.video_metadata_dataset.video_chapters_v2` (
    source_video_uri STRING, chapter_number INT64, title STRING, summary STRING, start_time_seconds FLOAT64, end_time_seconds FLOAT64
);

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.video_metadata_dataset.video_chunks_v2` (
    chunk_id STRING, source_video_uri STRING, chapter_number INT64, chunk_number INT64, chunk_text STRING
);

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.video_metadata_dataset.video_transcript_words_v2` (
    source_video_uri STRING, word STRING, start_time_seconds FLOAT64, end_time_seconds FLOAT64
);

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.video_metadata_dataset.scene_embeddings` (
    video_id STRING, shot_id STRING, start_time FLOAT64, end_time FLOAT64, embedding ARRAY<FLOAT64>
);
```

### 2. Backend Deployment
Navigate to the backend/ directory and deploy to Cloud Run:
```
gcloud builds submit --tag gcr.io/YOUR_PROJECT/master-pipeline .

gcloud run deploy master-service \
    --image gcr.io/YOUR_PROJECT/master-pipeline \
    --region us-central1 --memory 4Gi --cpu 2 --timeout 3600 \
    --set-env-vars GCP_PROJECT=YOUR_PROJECT,GCP_LOCATION=us-central1,BIGQUERY_DATASET=video_metadata_dataset
```

### 3. Frontend Deployment
Navigate to the frontend/ directory and deploy the Streamlit app:
```
gcloud builds submit --tag gcr.io/YOUR_PROJECT/video-frontend .

gcloud run deploy video-frontend \
    --image gcr.io/YOUR_PROJECT/video-frontend \
    --region us-central1 --memory 2Gi \
    --allow-unauthenticated \
    --set-env-vars GCP_PROJECT=YOUR_PROJECT,GCP_LOCATION=us-central1,BIGQUERY_DATASET=video_metadata_dataset,VECTOR_SEARCH_INDEX_ENDPOINT="YOUR_ENDPOINT_ID",VECTOR_SEARCH_INDEX_ID="YOUR_INDEX_ID",VECTOR_SEARCH_DEPLOYED_INDEX_ID="YOUR_DEPLOYED_ID"
```

## Contributors
- Gagan Kaur
- Gino Filicetti

## License
This repository is licensed under Apache2 license. More info can be found [here](./LICENSE).