import os
import json
from io import BytesIO
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ----------------------------
# List folders in a bucket
# ----------------------------
def supa_list_folders(bucket: str, prefix: str = ""):
    response = supabase.storage.from_(bucket).list(path=prefix)
    return [item['name'] for item in response if item['metadata'].get('mimetype') is None]

# ----------------------------
# List files in a folder
# ----------------------------
def supa_list_files(bucket: str, prefix: str):
    response = supabase.storage.from_(bucket).list(path=prefix)
    return [item['name'] for item in response if item['metadata'].get('mimetype') is not None]

# ----------------------------
# Download JSON
# ----------------------------
def supa_download_json(bucket: str, path: str):
    try:
        res = supabase.storage.from_(bucket).download(path)
        return json.loads(res.decode("utf-8"))
    except Exception:
        return None

def supa_load_json(bucket: str, path: str):
    try:
        response = supabase.storage.from_(bucket).download(path)
        if isinstance(response, bytes):
            return json.loads(response.decode("utf-8"))
        elif isinstance(response, BytesIO):
            return json.load(response)
    except Exception as e:
        print(f"Failed to load {path}: {e}")
        return None

# ----------------------------
# Upload JSON
# ----------------------------
def supa_upload_json(bucket: str, path: str, data: dict):
    try:
        buffer = BytesIO(json.dumps(data, indent=2).encode("utf-8"))
        supabase.storage.from_(bucket).upload(path, buffer, {"content-type": "application/json", "upsert": True})
        return True
    except Exception as e:
        print(f"[supa_upload_json] Error: {e}")
        return False

# ----------------------------
# Upload text
# ----------------------------
def supa_upload_text(bucket: str, path: str, content: str):
    try:
        buffer = BytesIO(content.encode("utf-8"))
        supabase.storage.from_(bucket).upload(path, buffer, {"content-type": "text/plain", "upsert": True})
        return True
    except Exception as e:
        print(f"[supa_upload_text] Error: {e}")
        return False

def supa_download_text(bucket: str, path: str):
    try:
        res = supabase.storage.from_(bucket).download(path)
        return res.decode("utf-8")
    except Exception:
        return None

# ----------------------------
# Upload CSV
# ----------------------------
def supa_upload_csv(bucket: str, path: str, df: pd.DataFrame):
    try:
        csv_str = df.to_csv(index=False)
        buffer = BytesIO(csv_str.encode("utf-8"))
        supabase.storage.from_(bucket).upload(path, buffer, {"content-type": "text/csv", "upsert": True})
        return True
    except Exception as e:
        print(f"[supa_upload_csv] Error: {e}")
        return False

# ----------------------------
# Upload raw file
# ----------------------------
def supa_upload_file(bucket: str, path: str, content: bytes, file_options: dict = None):
    try:
        file_options = file_options or {"content-type": "application/octet-stream"}
        supabase.storage.from_(bucket).upload(path, content, file_options=file_options)
        print(f"[✓] Uploaded to {bucket}/{path}")
        return True
    except Exception as e:
        print(f"[✗] Upload failed: {e}")
        return False

# ----------------------------
# Delete file
# ----------------------------
def supa_delete_file(bucket: str, path: str):
    try:
        supabase.storage.from_(bucket).remove([path])
        return True
    except Exception as e:
        print(f"[supa_delete_file] Error: {e}")
        return False
