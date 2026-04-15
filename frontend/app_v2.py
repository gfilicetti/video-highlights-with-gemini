import os 
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import pandas as pd
from google.cloud import bigquery
import google.auth
import google.auth.transport.requests
from datetime import timedelta

# --- Import Original Utils for Text Search ---
try:
    from embedding_util_v2 import generate_embeddings_batch
    from vector_search_util import find_neighbors
except ImportError as e:
    st.error(f"Failed to import utility functions. Error: {e}")
    st.stop()

# --- Constants ---
GCP_PROJECT = os.environ.get("GCP_PROJECT")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", "video_metadata_dataset")

# Table References
MOMENTS_TABLE = os.environ.get("MOMENTS_TABLE", "scene_embeddings")
SCENE_EMBEDDINGS_TABLE = f"{GCP_PROJECT}.{BIGQUERY_DATASET}.{MOMENTS_TABLE}"

_CHAPTERS_TABLE_NAME = os.environ.get("CHAPTERS_TABLE", "video_chapters_v2")
CHAPTERS_TABLE = f"{GCP_PROJECT}.{BIGQUERY_DATASET}.{_CHAPTERS_TABLE_NAME}"

_CHUNKS_TABLE_NAME = os.environ.get("CHUNKS_TABLE", "video_chunks_v2")
CHUNKS_TABLE = f"{GCP_PROJECT}.{BIGQUERY_DATASET}.{_CHUNKS_TABLE_NAME}"

# --- Page Config ---
st.set_page_config(page_title="AI Content Intelligence Engine", layout="wide")
st.title("🎬 AI Content Intelligence Engine")
st.markdown("Browse automatically generated video highlights, or search the entire library for specific quotes and topics.")

@st.cache_resource
def get_bq_client():
    return bigquery.Client(project=GCP_PROJECT)

client = get_bq_client()

@st.cache_data(ttl=3600)
def get_signed_video_url(gcs_uri: str):
    from google.cloud import storage 
    try:
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        storage_client = storage.Client(credentials=creds)
        bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
        blob = storage_client.bucket(bucket_name).blob(blob_name)
        return blob.generate_signed_url(
            version="v4", expiration=timedelta(hours=1), method="GET",
            service_account_email=creds.service_account_email, access_token=creds.token
        )
    except Exception as e:
        return None

def clear_search_results():
    for key in list(st.session_state.keys()):
        if key.startswith('url_') or key.startswith('start_time_'):
            del st.session_state[key]

# --- UI Tabs ---
tab1, tab2 = st.tabs(["🌟 Memorable Moments Gallery", "🔎 Keyword Search & Directory"])

# ==========================================
# TAB 1: MEMORABLE MOMENTS (Video Selection -> Up to 3 Clips)
# ==========================================
with tab1:
    st.subheader("🌟 Top Memorable Moments")
    st.markdown("Select a video from the library to instantly view its top curated highlights.")
    
    try:
        # 1. Fetch distinct videos that have memorable moments
        videos_query = f"SELECT DISTINCT source_video_uri FROM `{SCENE_EMBEDDINGS_TABLE}`"
        vids_df = client.query(videos_query).to_dataframe()

        if not vids_df.empty:
            vids = vids_df['source_video_uri'].tolist()
            # Clean up names for the dropdown (e.g., "demo1.mp4")
            display_names = {v.split("/")[-1]: v for v in vids}
            
            # The Dropdown Selector
            selected_display = st.selectbox("Select a Video:", list(display_names.keys()), key="hl_vid")
            selected_uri = display_names[selected_display]

            # 2. Fetch UP TO 3 moments for the selected video
            hl_query = f"""
                SELECT label, reason, start_time, end_time
                FROM `{SCENE_EMBEDDINGS_TABLE}`
                WHERE source_video_uri = @uri
                ORDER BY start_time ASC
                LIMIT 3
            """
            job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("uri", "STRING", selected_uri)])
            hl_df = client.query(hl_query, job_config=job_config).to_dataframe()

            st.markdown(f"**Showing top {len(hl_df)} moments for: {selected_display}**")
            st.divider()

            if not hl_df.empty:
                for _, row in hl_df.iterrows():
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        url = get_signed_video_url(selected_uri)
                        if url:
                            # Cue the video player exactly to the highlight start time
                            st.video(url, start_time=int(row['start_time']))
                    with col2:
                        st.write(f"### {row['label']}")
                        st.write(f"**Description:** {row['reason']}")
                        st.info(f"Clip Timestamp: {row['start_time']}s - {row['end_time']}s")
                    st.divider()
            else:
                st.info("No highlights found for this specific video.")
        else:
            st.info("No memorable moments processed yet. Upload a video to get started!")
    except Exception as e:
        st.error(f"Failed to load memorable moments: {e}")

# ==========================================
# TAB 2: SEARCH & CHAPTER DIRECTORY
# ==========================================
with tab2:
    st.subheader("🔎 Search Library")
    
    # --- TOP SECTION: SEARCH BAR ---
    text_query = st.text_input("Enter keywords, quotes, or topics:", key="text_search", on_change=clear_search_results)

    if text_query:
        with st.spinner(f"Searching library for '{text_query}'..."):
            try:
                # 1. Embed query
                query_embedding = generate_embeddings_batch([text_query])[0]
                
                # --- DIRECT DEBUG QUERY ---
                from google.cloud import aiplatform
                endpoint_name = os.environ.get("VECTOR_SEARCH_INDEX_ENDPOINT")
                deployed_id = os.environ.get("VECTOR_SEARCH_DEPLOYED_INDEX_ID")
                
                if not endpoint_name or not deployed_id:
                    st.error("🚨 CRITICAL: Vector Search Environment Variables are missing!")
                    st.stop()
                
                my_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=endpoint_name)
                
                try:
                    response = my_endpoint.find_neighbors(
                        queries=[query_embedding],
                        deployed_index_id=deployed_id,
                        num_neighbors=5
                    )
                    neighbors = response[0] if response else[]
                except Exception as vertex_error:
                    st.error(f"🚨 VERTEX AI REJECTED THE SEARCH: {vertex_error}")
                    st.stop()
                # -------------------------

                if neighbors:
                    matched_chunk_ids = [n.id for n in neighbors]
                    
                    if matched_chunk_ids:
                        query = f"""
                            SELECT chunks.chunk_id, chunks.source_video_uri, chunks.chapter_number, 
                                   chunks.chunk_text AS matched_chunk, chapters.title, chapters.start_time_seconds
                            FROM `{CHUNKS_TABLE}` AS chunks
                            JOIN `{CHAPTERS_TABLE}` AS chapters
                              ON chunks.source_video_uri = chapters.source_video_uri AND chunks.chapter_number = chapters.chapter_number
                            WHERE chunks.chunk_id IN UNNEST(@chunk_ids)
                        """
                        job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ArrayQueryParameter("chunk_ids", "STRING", matched_chunk_ids)])
                        search_results_df = client.query(query, job_config=job_config).to_dataframe()

                        st.success(f"Found {len(search_results_df)} relevant clips.")

                        for index, row in search_results_df.iterrows():
                            colA, colB = st.columns([1, 2])
                            with colA:
                                url = get_signed_video_url(row['source_video_uri'])
                                if url:
                                    st.video(url, start_time=int(row['start_time_seconds']))
                            with colB:
                                st.markdown(f"**Chapter {row['chapter_number']}: {row['title']}**")
                                st.markdown(f"*(Video: {row['source_video_uri'].split('/')[-1]})*")
                                st.info(f"...{row['matched_chunk']}...")
                            st.markdown("---")
                    else:
                        st.warning("No highly relevant clips found.")
                else:
                    st.warning("Vertex AI returned 0 results. The index is likely still syncing.")
            except Exception as e:
                st.error(f"General Search error: {e}")

    # --- BOTTOM SECTION: CHAPTERS TABLE ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader("📚 Video Directory")
    st.markdown("A complete list of all videos, chapters, and summaries currently in the database.")
    
    try:
        ch_query = f"""
            SELECT 
                source_video_uri as Video_File, 
                chapter_number as Chapter, 
                title as Title, 
                summary as Summary, 
                start_time_seconds as Start_Time, 
                end_time_seconds as End_Time
            FROM `{CHAPTERS_TABLE}`
            ORDER BY source_video_uri DESC, chapter_number ASC
        """
        df_all_chapters = client.query(ch_query).to_dataframe()
        
        if not df_all_chapters.empty:
            # Clean up the Video URI to just show the filename for readability
            df_all_chapters['Video_File'] = df_all_chapters['Video_File'].apply(lambda x: x.split('/')[-1])
            
            # Render the dataframe cleanly
            st.dataframe(
                df_all_chapters, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Start_Time": st.column_config.NumberColumn(format="%d s"),
                    "End_Time": st.column_config.NumberColumn(format="%d s"),
                }
            )
        else:
            st.info("No chapters processed yet.")
    except Exception as e:
        st.error(f"Error loading video directory: {e}")