import json
from pathlib import Path

from src.timeline_builder import TimelineBuilder
from src.pexels_api import PexelsAPI
from config import VOICE_FILE, ORIGINAL_IMAGES_DIR


PLAN_FILE = Path("visual_review_plan.json")


def _placeholder(prefix, media_id, ext):
    return str(Path(f"__PEXELS__/{prefix}_{media_id}{ext}"))


def build_review_plan():
    builder = TimelineBuilder(
        audio_file=VOICE_FILE,
        images_dir=ORIGINAL_IMAGES_DIR,
    )

    # Replace only the download-producing methods. Pexels API search itself is
    # still used, but no stock media is written to disk during review planning.
    def review_stock_video(query):
        item = builder.pexels.best_video(query)
        if not item:
            return None

        return {
            "media": _placeholder("video", item["id"], ".mp4"),
            "media_type": "video",
            "source_type": "stock_video",
            "label": "STOCK VIDEO",
            "score": None,
            "pexels_id": item["id"],
            "pexels_url": item["url"],
            "query": query,
        }

    def review_stock_image(query):
        # Reuse the existing 15% stock-image selection rule.
        if not builder.should_try_stock_image():
            return None

        item = builder.pexels.best_image(query)
        if not item:
            return None

        builder.stock_image_count += 1

        return {
            "media": _placeholder("image", item["id"], ".jpg"),
            "media_type": "image",
            "source_type": "stock_image",
            "label": "STOCK IMAGE",
            "score": None,
            "pexels_id": item["id"],
            "pexels_url": item["url"],
            "query": query,
        }

    builder.find_stock_video = review_stock_video
    builder.find_stock_image = review_stock_image

    # Keep original selection unchanged.
    timeline = builder.build()

    plan = []
    for item in timeline:
        media = str(item.get("media", ""))
        is_stock = media.startswith("__PEXELS__")
        entry = dict(item)

        if is_stock:
            name = Path(media).name
            bits = name.rsplit("_", 1)
            if len(bits) == 2:
                try:
                    pid = int(bits[1].split(".", 1)[0])
                except ValueError:
                    pid = None
            else:
                pid = None

            entry["pexels_id"] = pid
            entry["downloaded"] = False
            # Query is present only in the generated source metadata, so recover
            # it from the timeline item's selected query when available.
            entry["query"] = item.get("query") or ""
        else:
            entry["pexels_id"] = None
            entry["downloaded"] = True
            entry["query"] = ""

        # Review status is deliberately conservative:
        # - original with an acceptable matcher score => ALMOST OK
        # - concrete Pexels ID => ALMOST OK
        # - anything unresolved/generic => INCOMPLETE
        score = item.get("score")
        source = item.get("source_type")
        query = str(entry.get("query") or "").strip()

        if source == "original" and (score is None or float(score) >= 0.17):
            entry["review_status"] = "ALMOST OK"
        elif source in {"stock_video", "stock_image"} and entry["pexels_id"]:
            entry["review_status"] = "ALMOST OK"
        else:
            entry["review_status"] = "INCOMPLETE"

        plan.append(entry)

    payload = {
        "version": 1,
        "voice_file": str(VOICE_FILE),
        "timeline_items": plan,
    }
    PLAN_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Review plan saved: {PLAN_FILE.resolve()}")
    print(f"Timeline items: {len(plan)}")
    return plan


if __name__ == "__main__":
    build_review_plan()
