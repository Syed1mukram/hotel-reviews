from pathlib import Path
from collections import deque
import hashlib
import requests

from config import (
    PEXELS_API_KEY,
    STOCK_VIDEO_DIR,
    PEXELS_RESULTS,
)


VIDEO_SEARCH_URL = (
    "https://api.pexels.com/videos/search"
)

IMAGE_SEARCH_URL = (
    "https://api.pexels.com/v1/search"
)


class PexelsAPI:

    def _safe_get(self, url, **kwargs):
        """GET without crashing the entire timeline on a Pexels HTTP error."""
        try:
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            print(f"[PEXELS] Request failed: {exc}")
            return None

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({
            "Authorization": PEXELS_API_KEY
        })

        STOCK_VIDEO_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        # Images will be stored here
        self.stock_image_dir = (
            STOCK_VIDEO_DIR.parent
            / "stock_images"
        )

        self.stock_image_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # Used during THIS video
        self.used_videos = set()
        self.used_images = set()

        self.recent_videos = deque(
            maxlen=50
        )

        self.recent_images = deque(
            maxlen=50
        )

    # =========================================================
    # KEY
    # =========================================================

    def _key(self, url):

        return hashlib.md5(
            url.encode("utf8")
        ).hexdigest()

    # =========================================================
    # VIDEO SEARCH
    # =========================================================

    def search(
        self,
        query,
        per_page=None,
    ):

        if not PEXELS_API_KEY:

            raise RuntimeError(
                "PEXELS_API_KEY missing "
                "in .env"
            )

        if per_page is None:
            per_page = PEXELS_RESULTS

        response = self._safe_get(
            VIDEO_SEARCH_URL,
            params={
                "query": query,
                "per_page": per_page,
                "orientation": "landscape",
            },
            timeout=30,
        )

        if response is None:
            return []

        return response.json().get(
            "videos",
            []
        )

    # =========================================================
    # BEST VIDEO
    # =========================================================

    def best_video(
        self,
        query,
    ):

        videos = self.search(query)

        if not videos:
            return None

        candidates = []

        for video in videos:

            files = video.get(
                "video_files",
                []
            )

            if not files:
                continue

            suitable = [
                f for f in files
                if f.get("width", 0) >= 1920
            ]

            if not suitable:
                suitable = files

            best = max(
                suitable,
                key=lambda f: (
                    f.get("width", 0),
                    f.get("height", 0)
                )
            )

            url = best.get("link")

            if not url:
                continue

            key = self._key(url)

            if key in self.used_videos:
                continue

            if key in self.recent_videos:
                continue

            candidates.append({
                "id": video.get("id"),
                "url": url,
                "width": best.get(
                    "width",
                    0
                ),
                "height": best.get(
                    "height",
                    0
                ),
                "key": key,
            })

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: (
                x["width"],
                x["height"]
            ),
            reverse=True
        )

        selected = candidates[0]

        self.used_videos.add(
            selected["key"]
        )

        self.recent_videos.append(
            selected["key"]
        )

        return selected

    # =========================================================
    # DOWNLOAD VIDEO
    # =========================================================

    def download(
        self,
        query,
    ):

        video = self.best_video(
            query
        )

        if video is None:
            return None

        url = video["url"]

        filename = (
            str(video["id"])
            + ".mp4"
        )

        output = (
            STOCK_VIDEO_DIR
            / filename
        )

        if output.exists():

            return output

        print(
            f"[STOCK VIDEO] "
            f"Downloading: {query}"
        )

        response = self._safe_get(
            url,
            stream=True,
            timeout=60,
        )

        if response is None:
            return None

        with open(
            output,
            "wb"
        ) as f:

            for chunk in response.iter_content(
                1024 * 1024
            ):

                if chunk:
                    f.write(chunk)

        return output

    # =========================================================
    # IMAGE SEARCH
    # =========================================================

    def search_images(
        self,
        query,
        per_page=10,
    ):

        if not PEXELS_API_KEY:

            raise RuntimeError(
                "PEXELS_API_KEY missing "
                "in .env"
            )

        response = self._safe_get(
            IMAGE_SEARCH_URL,
            params={
                "query": query,
                "per_page": per_page,
                "orientation": "landscape",
            },
            timeout=30,
        )

        if response is None:
            return []

        return response.json().get(
            "photos",
            []
        )

    # =========================================================
    # BEST IMAGE
    # =========================================================

    def best_image(
        self,
        query,
    ):

        photos = self.search_images(
            query,
            per_page=10,
        )

        if not photos:
            return None

        candidates = []

        for photo in photos:

            src = photo.get(
                "src",
                {}
            )

            # Prefer large landscape image
            url = (
                src.get("large2x")
                or src.get("large")
                or src.get("original")
            )

            if not url:
                continue

            key = self._key(url)

            # STRICT ONE-TIME USE
            if key in self.used_images:
                continue

            if key in self.recent_images:
                continue

            width = photo.get(
                "width",
                0
            )

            height = photo.get(
                "height",
                0
            )

            candidates.append({
                "id": photo.get("id"),
                "url": url,
                "width": width,
                "height": height,
                "key": key,
            })

        if not candidates:
            return None

        # Prefer large landscape images
        candidates.sort(
            key=lambda x: (
                x["width"],
                x["height"]
            ),
            reverse=True
        )

        selected = candidates[0]

        self.used_images.add(
            selected["key"]
        )

        self.recent_images.append(
            selected["key"]
        )

        return selected

    # =========================================================
    # DOWNLOAD IMAGE
    # =========================================================

    def download_image(
        self,
        query,
    ):

        image = self.best_image(
            query
        )

        if image is None:
            return None

        url = image["url"]

        filename = (
            str(image["id"])
            + ".jpg"
        )

        output = (
            self.stock_image_dir
            / filename
        )

        if output.exists():

            return output

        print(
            f"[STOCK IMAGE] "
            f"Downloading: {query}"
        )

        response = self._safe_get(
            url,
            stream=True,
            timeout=60,
        )

        if response is None:
            return None

        with open(
            output,
            "wb"
        ) as f:

            for chunk in response.iter_content(
                1024 * 1024
            ):

                if chunk:
                    f.write(chunk)

        return output

    # =========================================================
    # RESET
    # =========================================================

    def reset(self):

        self.used_videos.clear()
        self.used_images.clear()

        self.recent_videos.clear()
        self.recent_images.clear()