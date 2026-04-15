import os
import vertexai
from typing import List, Optional
from vertexai.language_models import TextEmbeddingModel
from google import genai
from google.genai import types

# --- Configuration ---
GCP_PROJECT = os.environ.get("GCP_PROJECT")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
TEXT_MODEL_NAME = "text-embedding-005"
MM_MODEL_NAME = "gemini-embedding-2-preview"

_is_vertex_initialized = False

def init_vertex_ai():
    """Initializes the standard Vertex AI SDK for Text Embeddings."""
    global _is_vertex_initialized
    if not _is_vertex_initialized:
        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
        _is_vertex_initialized = True

# ==========================================
# 1. TEXT EMBEDDINGS (For Chapters/Transcript)
# ==========================================
def generate_embeddings_batch(texts: List[str]) -> Optional[List[List[float]]]:
    try:
        init_vertex_ai()
        model = TextEmbeddingModel.from_pretrained(TEXT_MODEL_NAME)
        BATCH_SIZE = 5
        all_embeddings =[]

        for i in range(0, len(texts), BATCH_SIZE):
            batch_of_texts = texts[i:i + BATCH_SIZE]
            response = model.get_embeddings(batch_of_texts)
            all_embeddings.extend([emb.values for emb in response])
        
        return all_embeddings
    except Exception as e:
        print(f"Error in text embedding: {e}")
        return None

# ==========================================
# 2. MULTIMODAL EMBEDDINGS (For Memorable Moments)
# ==========================================
def get_multimodal_video_embedding(project_id, location, video_uri, start_sec, end_sec):
    """Generates multimodal embeddings using the official genai SDK."""
    from google import genai
    from google.genai import types
    
    try:
        client = genai.Client(vertexai=True, project=project_id, location=location)
        
        # Safely convert timestamps to float
        start = float(start_sec) if start_sec is not None else 0.0
        end = float(end_sec) if end_sec is not None else 10.0
        
        video_part = types.Part.from_uri(file_uri=video_uri, mime_type="video/mp4")
        video_part.video_metadata = types.VideoMetadata(
            start_offset=f"{start}s",
            end_offset=f"{end}s"
        )
        
        result = client.models.embed_content(
            model="gemini-embedding-2-preview",
            contents=[video_part]
        )
        
        return result.embeddings[0].values
        
    except Exception as e:
        print(f"Multimodal embedding failed for {start_sec}s-{end_sec}s: {e}")
        return None