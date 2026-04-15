import os
import time
from typing import List, Dict
from google.cloud import storage, videointelligence, bigquery
from google import genai
from google.genai import types
from moviepy import VideoFileClip, concatenate_videoclips

# --- Configuration ---
PROJECT_ID = ""
LOCATION = ""
GCS_BUCKET = ""
BQ_DATASET = "video_metadata_dataset"
BQ_TABLE = "scene_embeddings"

class VideoHighlightGenerator:
    def __init__(self):
        self.bq_client = bigquery.Client()
        self.video_client = videointelligence.VideoIntelligenceServiceClient()
        self.ai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        self.embedding_model = "gemini-embedding-2-preview"

    def detect_shots(self, gcs_uri: str) -> List[Dict]:
        print("Step 1: Segmenting video into shots...")
        features = [videointelligence.Feature.SHOT_CHANGE_DETECTION]
        operation = self.video_client.annotate_video(request={"features": features, "input_uri": gcs_uri})
        result = operation.result(timeout=600)
        return [{"shot_id": f"shot_{i}", 
                 "start_time": s.start_time_offset.total_seconds(), 
                 "end_time": s.end_time_offset.total_seconds()} 
                for i, s in enumerate(result.annotation_results[0].shot_annotations)]

    def embed_video_clip(self, local_clip_path: str) -> List[float]:
        """Sends compressed video bytes to Gemini."""
        with open(local_clip_path, "rb") as f:
            video_bytes = f.read()
        
        if len(video_bytes) > 20 * 1024 * 1024:
            print("Warning: Clip too large, skipping...")
            return None

        result = self.ai_client.models.embed_content(
            model=self.embedding_model,
            contents=[types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")]
        )
        return result.embeddings[0].values

    def store_in_bigquery(self, video_id: str, shot: Dict, embedding: List[float]):
        if not embedding: return
        table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
        rows_to_insert = [{
            "video_id": video_id, 
            "shot_id": shot["shot_id"],
            "start_time": shot["start_time"], 
            "end_time": shot["end_time"],
            "embedding": embedding 
        }]
        errors = self.bq_client.insert_rows_json(table_id, rows_to_insert)
        if errors: print(f"BigQuery Insert Error: {errors}")

    def recommend_scenes_for_user(self, text_query: str) -> List[Dict]:
        """Matches text embeddings against video embeddings in BigQuery."""
        text_result = self.ai_client.models.embed_content(
            model=self.embedding_model, contents=[text_query]
        )
        user_emb = text_result.embeddings[0].values
        emb_str = str(user_emb)
        
        query = f"""
            SELECT base.start_time, base.end_time, distance
            FROM VECTOR_SEARCH(
              TABLE `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`,
              'embedding',
              (SELECT {emb_str} AS user_emb),
              top_k => 3
            )
        """
        print(f"Executing Vector Search for: '{text_query}'...")
        query_job = self.bq_client.query(query)
        return [dict(row) for row in query_job]

    def assemble_highlights(self, full_video, recommended_shots: List[Dict], output_filename: str):
        """Cuts and stitches the recommended scenes together."""
        print(f"Step 4: Assembling {len(recommended_shots)} clips into highlight reel...")
        clips = []
        for r in recommended_shots:
            # Using subclipped and resized for MoviePy 2.0
            clip = full_video.subclipped(r["start_time"], r["end_time"])
            clips.append(clip)
        
        if clips:
            final_clip = concatenate_videoclips(clips)
            final_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac")
            print(f"Success! Saved to {output_filename}")
        else:
            print("No clips were found to assemble.")

# --- EXECUTION ---
if __name__ == "__main__":
    gen = VideoHighlightGenerator()
    local_video = "KOC_162_20260223_OCONNOR_TEST9-lowres.mp4"
    # Make sure this URI matches your actual bucket
    gcs_video_uri = f"gs://yahoo-testing-video-bucket/{local_video}"
    
    # 1. Get shot boundaries
    shots = gen.detect_shots(gcs_video_uri)
    full_video = VideoFileClip(local_video)
    
    # 2. Process shots (Limit to 10 for speed)
    print("Step 2: Processing shots and generating multimodal embeddings...")
    for shot in shots[:10]:
        duration = shot['end_time'] - shot['start_time']
        
        # INCREASE THIS TO 120.0 to allow your 72s shot to be processed
        if 0.5 <= duration <= 120.0:
            temp_path = f"temp_{shot['shot_id']}.mp4"
            
            print(f"Creating clip for {shot['shot_id']} (Duration: {duration:.2f}s)...")
            # Create the file
            clip = full_video.subclipped(shot["start_time"], shot["end_time"]).resized(height=360)
            clip.write_videofile(temp_path, codec="libx264", bitrate="500k", audio_codec="aac", logger=None)
            
            # EVERYTHING BELOW MUST BE INDENTED INSIDE THE "IF"
            if os.path.exists(temp_path):
                print(f"Embedding {shot['shot_id']}...")
                emb = gen.embed_video_clip(temp_path)
                gen.store_in_bigquery("video_001", shot, emb)
                
                # Clean up the file after embedding is sent
                os.remove(temp_path)
                time.sleep(1) # Safety for API limits
            else:
                print(f"Error: {temp_path} was not created successfully.")
        else:
            print(f"Skipping {shot['shot_id']}: duration {duration:.2f}s (outside 0.5s-120s limit)")

    # 3. Search
    print("Step 3: Searching for memorable moments...")
    recs = gen.recommend_scenes_for_user("exciting action highlights and key moments")
    
    # 4. Assemble
    if recs:
        gen.assemble_highlights(full_video, recs, "memorable_highlights.mp4")
    else:
        print("No recommendations found.")