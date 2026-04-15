import os
import json
import logging
import traceback
import time
import re
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

# --- Utils ---
from video_intelligence_util_v2 import transcribe_video
from bigquery_util_v2 import (
    delete_existing_chapters, save_chapters_to_bigquery, 
    save_chunks_to_bigquery, save_transcript_words,
    save_memorable_moments_to_bigquery 
)
from vector_search_util import upsert_data_to_vector_search
from gemini_util_v2 import generate_consolidated_chapters, identify_memorable_moments
from embedding_util_v2 import generate_embeddings_batch, get_multimodal_video_embedding
from google.cloud import storage, bigquery
import google.api_core.exceptions

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# --- Environment Variables ---
GCP_PROJECT = os.environ.get("GCP_PROJECT")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", "video_metadata_dataset")

# Tables
CHAPTERS_TABLE = os.environ.get("CHAPTERS_TABLE", "video_chapters_v2")
CHUNKS_TABLE = os.environ.get("CHUNKS_TABLE", "video_chunks_v2")
WORDS_TABLE = os.environ.get("WORDS_TABLE", "video_transcript_words_v2")
MOMENTS_TABLE = os.environ.get("MOMENTS_TABLE", "scene_embeddings") 

def sanitize_filename(filename: str):
    base, ext = os.path.splitext(filename)
    sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '', base.replace(' ', '_').replace("'", ""))
    return f"{sanitized}{ext}"

def _run_processing_pipeline_v2(bucket_name, original_file_name):
    gcs_uri = f"gs://{bucket_name}/{original_file_name}"
    
    # 1. Lease File Logic
    storage_client = storage.Client()
    source_blob = storage_client.bucket(bucket_name).blob(original_file_name)
    sanitized_name = sanitize_filename(original_file_name)
    new_name = f"processing/{sanitized_name}"
    try:
        processing_blob = storage_client.bucket(bucket_name).rename_blob(source_blob, new_name)
    except google.api_core.exceptions.NotFound:
        return
    
    source_gcs_uri = f"gs://{bucket_name}/{processing_blob.name}"
    final_uri = f"gs://{bucket_name}/processed/{sanitized_name}"
    logging.info(f"--- UNIFIED PIPELINE START: {final_uri} ---")

    try:
        delete_existing_chapters(GCP_PROJECT, BIGQUERY_DATASET, CHAPTERS_TABLE, final_uri)
        delete_existing_chapters(GCP_PROJECT, BIGQUERY_DATASET, CHUNKS_TABLE, final_uri)
        delete_existing_chapters(GCP_PROJECT, BIGQUERY_DATASET, WORDS_TABLE, final_uri)
        delete_existing_chapters(GCP_PROJECT, BIGQUERY_DATASET, MOMENTS_TABLE, final_uri) 

        # --- TRACK A: DIALOGUE & CHAPTER CAPABILITY ---
        logging.info("Step 1: Transcribing video...")
        _, transcript_words = transcribe_video(source_gcs_uri)
        if not transcript_words: raise ValueError("No transcript generated.")

        logging.info("Step 2: Saving raw transcript...")
        for word in transcript_words: word['source_video_uri'] = final_uri
        save_transcript_words(GCP_PROJECT, BIGQUERY_DATASET, WORDS_TABLE, transcript_words)

        transcript_with_timestamps = " ".join([f"{w.get('word', '')}({w.get('start_time_seconds', 0)})" for w in transcript_words])
        
        logging.info("Step 3: Chapterizing & Chunking Transcript...")
        chapters = generate_consolidated_chapters(GCP_PROJECT, GCP_LOCATION, transcript_with_timestamps)
        
        chapters_for_bq, chunks_for_bq, vector_search_datapoints = [], [],[]
        
        for i, ch in enumerate(chapters):
            start, end = ch.get('start_time'), ch.get('end_time')
            if start is None or end is None: continue
            
            chapters_for_bq.append({
                "source_video_uri": final_uri, "chapter_number": i + 1,
                "title": ch.get('title'), "summary": ch.get('summary'),
                "start_time_seconds": float(start), "end_time_seconds": float(end)
            })

            ch_words = [w['word'] for w in transcript_words if start <= w.get('start_time_seconds', 9999) < end]
            ch_text = " ".join(ch_words).split()
            text_chunks = [" ".join(ch_text[j:j+50]) for j in range(0, len(ch_text), 40)]
            
            if text_chunks:
                chunk_embs = generate_embeddings_batch(text_chunks) 
                for j, chunk in enumerate(text_chunks):
                    chunk_id = f"{final_uri}|ch{i+1}|pk{j+1}"
                    chunks_for_bq.append({"chunk_id": chunk_id, "source_video_uri": final_uri, "chapter_number": i+1, "chunk_number": j+1, "chunk_text": chunk})
                    vector_search_datapoints.append({"datapoint_id": chunk_id, "feature_vector": chunk_embs[j]})

        # --- TRACK B: THE MULTIMODAL MEMORABLE MOMENTS ---
        logging.info("Step 4: Identifying & Embedding Memorable Moments (Multimodal)...")
        moments = identify_memorable_moments(GCP_PROJECT, GCP_LOCATION, source_gcs_uri)
        moments_for_bq =[]
        
        for idx, m in enumerate(moments):
            vector = get_multimodal_video_embedding(GCP_PROJECT, GCP_LOCATION, source_gcs_uri, m.get('start_sec', 0), m.get('end_sec', 10))
            if vector:
                moments_for_bq.append({
                    "source_video_uri": final_uri,
                    "moment_id": f"{sanitized_name}|moment|{idx}",
                    "label": m.get('label', f"Moment {idx}"),
                    "reason": m.get('reason', ''),
                    "start_time": float(m.get('start_sec', 0)),
                    "end_time": float(m.get('end_sec', 10)),
                    "embedding": vector
                })
                time.sleep(2) 

        # --- FINAL SAVE ---
        logging.info("Step 5: Saving all Dual-Track Data...")
        if chapters_for_bq: save_chapters_to_bigquery(GCP_PROJECT, BIGQUERY_DATASET, CHAPTERS_TABLE, chapters_for_bq)
        if chunks_for_bq: save_chunks_to_bigquery(GCP_PROJECT, BIGQUERY_DATASET, CHUNKS_TABLE, chunks_for_bq)
        if vector_search_datapoints: upsert_data_to_vector_search(vector_search_datapoints)
        if moments_for_bq:
            bq_client = bigquery.Client(project=GCP_PROJECT)
            bq_client.insert_rows_json(f"{GCP_PROJECT}.{BIGQUERY_DATASET}.{MOMENTS_TABLE}", moments_for_bq)

        logging.info("Moving file to processed folder...")
        bucket = storage_client.bucket(bucket_name)
        new_blob_name = f"processed/{sanitized_name}"
        
        # Copy to new location
        bucket.copy_blob(processing_blob, bucket, new_blob_name)
        
        # Delete original (Ignore errors if GCS already cleaned it up)
        try:
            processing_blob.reload() 
            processing_blob.delete()
        except google.api_core.exceptions.NotFound:
            logging.info("Original blob already deleted.")
            
        logging.info("--- PIPELINE SUCCESS ---")

    except Exception as e:
        logging.error(f"CRITICAL ERROR: {traceback.format_exc()}")


@app.route("/", methods=["POST"])
def index():
    try:
        event = request.get_json()
        data = event.get('data', event)
        bucket, name = data.get('bucket'), data.get('name')
        
        if bucket and name:
            if '/' in name:
                logging.info(f"Ignoring file in subfolder: {name}")
                return "Ignored", 204
                
            if name.lower().endswith(('.mp4', '.mov')):
                _run_processing_pipeline_v2(bucket, name)
                return "Processed", 204
        return "Ignored", 204
    except Exception:
        logging.error(traceback.format_exc())
        return "Error", 500