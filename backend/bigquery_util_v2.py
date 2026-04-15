from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError

# ==========================================
# 1. NEW: MEMORABLE MOMENTS LOGIC
# ==========================================
def save_memorable_moments_to_bigquery(project_id, dataset_id, table_id, moments_data):
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("source_video_uri", "STRING"),
            bigquery.SchemaField("moment_id", "STRING"),
            bigquery.SchemaField("label", "STRING"),
            bigquery.SchemaField("reason", "STRING"),
            bigquery.SchemaField("start_time", "FLOAT64"),
            bigquery.SchemaField("end_time", "FLOAT64"),
            bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
        ],
        write_disposition="WRITE_APPEND",
    )

    try:
        load_job = client.load_table_from_json(moments_data, table_ref, job_config=job_config)
        load_job.result()
        print(f"Successfully saved {len(moments_data)} memorable moments to BigQuery.")
    except Exception as e:
        print(f"Error saving moments to BigQuery: {e}")

# ==========================================
# 2. ORIGINAL: CHAPTERS, CHUNKS, AND WORDS LOGIC
# ==========================================
def delete_existing_chapters(project_id, dataset_id, table_id, video_uri):
    client = bigquery.Client(project=project_id)
    query = f"""
        DELETE FROM `{project_id}.{dataset_id}.{table_id}`
        WHERE source_video_uri = @video_uri
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("video_uri", "STRING", video_uri),
        ]
    )
    try:
        query_job = client.query(query, job_config=job_config)
        query_job.result() 
        print(f"Deleted existing data for {video_uri} from {table_id}.")
    except GoogleAPICallError as e:
        print(f"Could not delete existing data for {video_uri}. Error: {e}")

def save_chapters_to_bigquery(project_id, dataset_id, table_id, chapters_data):
    client = bigquery.Client(project=project_id)
    full_table_id = f"{project_id}.{dataset_id}.{table_id}"
    try:
        errors = client.insert_rows_json(full_table_id, chapters_data)
        if not errors:
            print(f"Successfully inserted {len(chapters_data)} chapters.")
        else:
            print(f"Errors inserting chapters: {errors}")
    except Exception as e:
        print(f"BigQuery error saving chapters: {e}")

def save_transcript_words(project_id, dataset_id, table_id, words_data):
    client = bigquery.Client(project=project_id)
    full_table_id = f"{project_id}.{dataset_id}.{table_id}"
    BATCH_SIZE = 500
    for i in range(0, len(words_data), BATCH_SIZE):
        batch = words_data[i:i + BATCH_SIZE]
        try:
            errors = client.insert_rows_json(full_table_id, batch)
            if errors: print(f"Errors inserting words: {errors}")
        except Exception as e:
            print(f"Error during batch insert: {e}")

def save_chunks_to_bigquery(project_id, dataset_id, table_id, chunks_data):
    client = bigquery.Client(project=project_id)
    full_table_id = f"{project_id}.{dataset_id}.{table_id}"
    BATCH_SIZE = 400 
    for i in range(0, len(chunks_data), BATCH_SIZE):
        batch = chunks_data[i:i + BATCH_SIZE]
        try:
            errors = client.insert_rows_json(full_table_id, batch)
            if errors: print(f"Errors inserting chunks: {errors}")
        except Exception as e:
            print(f"Error during chunk insert: {e}")