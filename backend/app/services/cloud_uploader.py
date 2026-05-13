"""Firebase upload helpers for pitch evaluation artifacts and results."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.api_core.exceptions import NotFound

logger = logging.getLogger(__name__)

_db = None
_bucket = None


def _load_service_account_config() -> dict:
    firebase_key_path = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")
    with open(firebase_key_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def init_firebase():
    """Initialize Firebase connection with service account credentials.
    
    Uses FIREBASE_KEY_PATH environment variable to locate the service account JSON.
    Returns Firestore database client.
    """
    global _db

    if _db is not None:
        return _db

    if not firebase_admin._apps:
        try:
            service_account = _load_service_account_config()
            storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET") or f"{service_account['project_id']}.appspot.com"
            cred = credentials.Certificate(service_account)
            firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})
            logger.info(
                "Firebase initialized with key from %s and storage bucket %s",
                os.getenv("FIREBASE_KEY_PATH", "firebase_key.json"),
                storage_bucket,
            )
        except Exception:
            logger.exception("Failed to initialize Firebase")
            return None

    _db = firestore.client()
    return _db


def init_storage_bucket():
    """Initialize and return the Firebase Storage bucket."""
    global _bucket

    if _bucket is not None:
        return _bucket

    init_firebase()
    if not firebase_admin._apps:
        return None

    try:
        bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
        _bucket = storage.bucket(bucket_name) if bucket_name else storage.bucket()
        return _bucket
    except Exception:
        logger.exception("Failed to initialize Firebase Storage bucket")
        return None


def upload_pitch_result(result: dict, video_title: str | None = None) -> bool:
    """Upload pitch evaluation result to Firebase Firestore.
    
    Args:
        result: Dictionary containing evaluation results with keys like:
                - summary (overall_score, confidence_score, investment_band, etc.)
                - chunk_reports
                - dashboard
                - request_id
    
    Returns:
        True if upload successful, False otherwise.
    """
    try:
        db = init_firebase()
        
        if db is None:
            logger.warning("Firebase not initialized, skipping cloud upload")
            return False

        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": result,
        }

        # Include video title/filename as top-level metadata if provided
        if video_title:
            payload["video_title"] = str(video_title)

        doc_ref = db.collection("pitch_evaluations").add(payload)
        logger.info(f"Pitch result uploaded to Firebase: {doc_ref}")
        return True
        
    except Exception:
        logger.exception("Cloud upload failed")
        return False


def upload_video_file_to_firebase_storage(file_path: str, destination_prefix: str = "edge_uploads") -> str | None:
    """Upload a video file to Firebase Storage and return its gs:// path."""
    try:
        bucket = init_storage_bucket()
        if bucket is None:
            logger.warning("Firebase Storage not initialized, skipping file upload")
            return None

        path = Path(file_path)
        if not path.exists():
            logger.error("Video file not found: %s", file_path)
            return None

        object_name = f"{destination_prefix}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{path.name}"
        blob = bucket.blob(object_name)
        blob.upload_from_filename(str(path), content_type="video/mp4")
        gs_path = f"gs://{bucket.name}/{object_name}"
        logger.info("Uploaded video to Firebase Storage: %s", gs_path)
        return gs_path

    except NotFound:
        logger.warning(
            "Firebase Storage bucket was not found. Enable Storage in Firebase or set FIREBASE_STORAGE_BUCKET to a valid bucket name."
        )
        return None
    except Exception:
        logger.exception("Failed to upload video to Firebase Storage")
        return None


def get_pitch_results(limit: int = 20) -> list:
    """Retrieve recent pitch evaluations from Firebase.
    
    Args:
        limit: Maximum number of results to retrieve (default: 20)
    
    Returns:
        List of pitch evaluation documents.
    """
    try:
        db = init_firebase()
        
        if db is None:
            logger.warning("Firebase not initialized, cannot retrieve results")
            return []

        docs = (
            db.collection("pitch_evaluations")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )

        results = []
        for doc in docs:
            results.append(doc.to_dict())
        
        logger.info(f"Retrieved {len(results)} pitch results from Firebase")
        return results
        
    except Exception:
        logger.exception("Failed to retrieve results from Firebase")
        return []
