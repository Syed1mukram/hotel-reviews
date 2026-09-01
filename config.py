from pathlib import Path
import os
from dotenv import load_dotenv

# Always load the .env that belongs to this project, even when
# Python is launched from another working directory (for example Kaggle).
ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env", override=True)

# ==========================================================
# PROJECT
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent

INPUT_DIR = ROOT_DIR / "input"
OUTPUT_DIR = ROOT_DIR / "output"
CACHE_DIR = ROOT_DIR / "cache"
ASSETS_DIR = ROOT_DIR / "assets"

# ==========================================================
# INPUT
# ==========================================================

HOTEL_DIR = INPUT_DIR

VOICE_FILE = INPUT_DIR / "voice.mp3"
ORIGINAL_IMAGES_DIR = INPUT_DIR / "images"

# ==========================================================
# CACHE
# ==========================================================

STOCK_VIDEO_DIR = CACHE_DIR / "stock"
STOCK_IMAGE_DIR = CACHE_DIR / "stock_images"
TEMP_DIR = CACHE_DIR / "temp"

# ==========================================================
# OUTPUT
# ==========================================================

OUTPUT_VIDEO = OUTPUT_DIR / "final_video.mp4"

# ==========================================================
# VIDEO
# ==========================================================

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

VIDEO_CODEC = "h264_nvenc"
AUDIO_CODEC = "aac"

PIXEL_FORMAT = "yuv420p"

PRESET = "medium"
CRF = 18

# ==========================================================
# IMAGES
# ==========================================================

IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".avif",
)

# ==========================================================
# WHISPER
# ==========================================================

WHISPER_MODEL = "base"
LANGUAGE = "en"

# ==========================================================
# PEXELS
# ==========================================================

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

PEXELS_RESULTS = 10

# ==========================================================
# STOCK VISUALS
# ==========================================================

STOCK_MIN_DURATION = 3
STOCK_MAX_DURATION = 15

# ==========================================================
# TIMELINE
# ==========================================================

TARGET_CLIP_DURATION = 4.0

MIN_SCENE_DURATION = 2.0

# ==========================================================
# VISUAL PRIORITY
# ==========================================================

# Original hotel image first.
# If unavailable -> stock video.
# If unavailable -> stock image.

USE_ORIGINAL_IMAGES = True
USE_STOCK_VIDEOS = True
USE_STOCK_IMAGES = True

# ==========================================================
# ONE-TIME USE
# ==========================================================

# Every visual can be used only once in the entire video.

NO_REPEAT_VISUALS = True

# ==========================================================
# STOCK LABEL
# ==========================================================

SHOW_STOCK_LABEL = True

STOCK_VIDEO_LABEL = "STOCK VIDEO"
STOCK_IMAGE_LABEL = "STOCK IMAGE"

# ==========================================================
# CREATE DIRECTORIES
# ==========================================================

for folder in (
    INPUT_DIR,
    OUTPUT_DIR,
    CACHE_DIR,
    ASSETS_DIR,
    HOTEL_DIR,
    ORIGINAL_IMAGES_DIR,
    STOCK_VIDEO_DIR,
    STOCK_IMAGE_DIR,
    TEMP_DIR,
):
    folder.mkdir(parents=True, exist_ok=True)