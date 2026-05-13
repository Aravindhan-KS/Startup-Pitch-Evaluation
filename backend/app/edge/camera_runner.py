"""File-based edge runner for pitch evaluation.

Instead of recording from a camera, this runner picks up an existing video file,
uploads the file to Firebase Storage, and sends it to the local backend for
computation.

Usage:
    python camera_runner.py --file path/to/video.mp4
    python camera_runner.py --watch

Environment variables:
    EDGE_INPUT_FILE: Path to a single video file to process
    EDGE_INPUT_DIR: Directory to scan for video files when not using --file
    EDGE_BACKEND_URL: Backend upload endpoint (default: http://127.0.0.1:8000/evaluate/upload)
    EDGE_OUTPUT_DIR: Directory for processed copies / staging files
    EDGE_WATCH_INTERVAL: Seconds between scans in watch mode
"""

import argparse
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
import sys

import requests

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.cloud_uploader import upload_pitch_result, upload_video_file_to_firebase_storage

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

BACKEND_URL = os.getenv("EDGE_BACKEND_URL", "http://127.0.0.1:8000/evaluate/upload")
INPUT_DIR = Path(os.getenv("EDGE_INPUT_DIR", "outputs/batch_input"))
OUTPUT_DIR = Path(os.getenv("EDGE_OUTPUT_DIR", "outputs/edge_staging"))
WATCH_INTERVAL_SEC = int(os.getenv("EDGE_WATCH_INTERVAL", "10"))

INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _discover_video_files(folder: Path) -> list[Path]:
    return sorted(
        [
            path for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv"}
        ],
        key=lambda path: path.stat().st_mtime,
    )


def _stage_file(source_path: Path) -> Path:
    destination = OUTPUT_DIR / f"{int(time.time())}_{source_path.name}"
    shutil.copy2(source_path, destination)
    return destination


def upload_and_evaluate_file(video_path: Path) -> bool:
    if not video_path.exists():
        logger.error("Video file not found: %s", video_path)
        return False

    staged_path = _stage_file(video_path)
    firebase_location = upload_video_file_to_firebase_storage(str(staged_path))
    if firebase_location:
        logger.info("Uploaded source file to Firebase Storage: %s", firebase_location)

    with staged_path.open("rb") as handle:
        files = {"video": (staged_path.name, handle, "video/mp4")}
        data = {
            "title": staged_path.stem,
            "transcript": "",
            "language_hint": "en",
            "slide_text": "",
            "founder_name": "",
            "startup_name": "",
            "sector": "",
            "stage": "",
        }

        try:
            logger.info("Sending file to backend for computation: %s", BACKEND_URL)
            response = requests.post(BACKEND_URL, files=files, data=data, timeout=900)
            response.raise_for_status()
            result = response.json()
            # Pass the original filename/title so the dashboard can display it
            try:
                upload_pitch_result(result, video_title=staged_path.name)
            except TypeError:
                # Fallback for older signatures
                upload_pitch_result(result)
            logger.info("Evaluation completed successfully")
            logger.info("Overall score: %s", result.get("summary", {}).get("overall_score"))
            logger.info("Investment band: %s", result.get("summary", {}).get("investment_band"))
            return True
        except requests.exceptions.RequestException:
            logger.exception("Evaluation failed")
            return False


def main():
    parser = argparse.ArgumentParser(description="File-based edge pitch evaluation runner")
    parser.add_argument("--file", dest="input_file", help="Video file to upload and evaluate")
    parser.add_argument("--watch", action="store_true", help="Watch EDGE_INPUT_DIR for new video files")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("EDGE FILE UPLOADER AND EVALUATOR")
    logger.info("=" * 60)
    logger.info("Backend URL: %s", BACKEND_URL)
    logger.info("Input directory: %s", INPUT_DIR)
    logger.info("Staging directory: %s", OUTPUT_DIR)
    logger.info("Watch interval: %ss", WATCH_INTERVAL_SEC)
    logger.info("=" * 60)

    if args.input_file:
        upload_and_evaluate_file(Path(args.input_file))
        return

    if args.watch:
        processed: set[Path] = set()
        try:
            while True:
                for video_file in _discover_video_files(INPUT_DIR):
                    if video_file in processed:
                        continue
                    if upload_and_evaluate_file(video_file):
                        processed.add(video_file)
                time.sleep(WATCH_INTERVAL_SEC)
        except KeyboardInterrupt:
            logger.info("\nFile watcher stopped by user")
        return

    video_files = _discover_video_files(INPUT_DIR)
    if not video_files:
        logger.error("No video files found in %s", INPUT_DIR)
        return

    upload_and_evaluate_file(video_files[-1])


if __name__ == "__main__":
    main()
