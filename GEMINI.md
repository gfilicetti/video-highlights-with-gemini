# Gemini Project Instructions: Video Highlights

## Project Mission
To provide a seamless, AI-driven video intelligence platform that automatically identifies highlights, generates logical chapters, and enables semantic search across video content using Google Gemini and Vertex AI.

## Tech Stack Mandates
- **Infrastructure:** All GCP infrastructure MUST be managed via Terraform in the `terraform/` directory. No manual resource creation.
- **Backend:** Python Flask/FastAPI (deployed on Cloud Run).
- **Frontend:** Streamlit (deployed on Cloud Run).
- **Storage:** Google Cloud Storage for raw and processed video assets.
- **Data Warehouse:** BigQuery for structured metadata and scene embeddings.
- **AI/ML:** Vertex AI Vector Search (for transcript RAG) and Gemini 2.5 (Pro for logic, Flash for vision).

## Development & Configuration
- **Configuration:** Use `.env` files for local development (mapped from `.env.template`). Use `python-dotenv` for loading.
- **Terraform Flow:** Always provide a `terraform.tfvars.example`. Never commit the actual `.tfvars`.
- **Reproducibility:** When adding new features, update both the local development scripts (`local-dev-highlights.py`) and the Cloud Run deployment logic.

## Architectural Patterns
- **Dual-Track Processing:**
    - **Track A (Dialogue):** Video Intelligence (Transcription) -> Gemini 2.5 Pro (Chapterization) -> Vertex AI Text Embeddings -> Vector Search.
    - **Track B (Visual):** Gemini 2.5 Flash (Memorable Moments) -> Multimodal Embeddings -> BigQuery.
- **Idempotency:** All data processing pipelines must check for and delete existing data for a given `video_uri` before inserting new results to prevent duplicates.

## Verification Standards
- Always run `terraform plan` before `apply`.
- Maintain a visually rich, interactive Streamlit UI that follows a clean, modern aesthetic.
