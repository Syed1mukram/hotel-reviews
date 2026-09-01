from pathlib import Path
import hashlib
import requests

from config import (
    STOCK_IMAGE_DIR,
    PEXELS_API_KEY,
    PEXELS_RESULTS,
)


SEARCH_URL = "https://api.pexels.com/v1/search"


class StockImageAPI:

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({
            "Authorization": PEXELS_API_KEY
        })

        STOCK_IMAGE_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        # Strict one-time-use tracking
        self.used_images = set()

    # -----------------------------------------------------

    def _key(self, url):

        return hashlib.md5(
            url.encode("utf-8")
        ).hexdigest()

    # -----------------------------------------------------

    def search(
        self,
        query,
        per_page=None,
    ):

        if not PEXELS_API_KEY:

            raise RuntimeError(
                "PEXELS_API_KEY missing in .env"
            )

        if per_page is None:
            per_page = PEXELS_RESULTS

        response = self.session.get(
            SEARCH_URL,
            params={
                "query": query,
                "per_page": per_page,
                "orientation": "landscape",
            },
            timeout=30,
        )

        response.raise_for_status()

        return response.json().get(
            "photos",
            []
        )

    # -----------------------------------------------------

    def best_image(self, query):

        photos = self.search(query)

        if not photos:
            return None

        candidates = []

        for photo in photos:

            src = photo.get(
                "src",
                {}
            )

            # Prefer large/original image
            url = (
                src.get("large2x")
                or src.get("large")
                or src.get("original")
            )

            if not url:
                continue

            key = self._key(url)

            # STRICT:
            # Never use same stock image twice
            if key in self.used_images:
                continue

            candidates.append({
                "id": photo.get("id"),
                "url": url,
                "key": key,
            })

        if not candidates:
            return None

        selected = candidates[0]

        self.used_images.add(
            selected["key"]
        )

        return selected

    # -----------------------------------------------------

    def download(self, query):

        image = self.best_image(
            query
        )

        if image is None:
            return None

        image_id = image["id"]

        output = (
            STOCK_IMAGE_DIR
            / f"{image_id}.jpg"
        )

        if output.exists():
            return output

        print(
            f"[STOCK IMAGE] "
            f"Downloading: {query}"
        )

        response = self.session.get(
            image["url"],
            stream=True,
            timeout=60,
        )

        response.raise_for_status()

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

    # -----------------------------------------------------

    def reset(self):

        self.used_images.clear()