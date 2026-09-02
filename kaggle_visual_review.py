import json
import os
import re
from pathlib import Path
from typing import Any

import gradio as gr
import requests

from config import PEXELS_API_KEY, VOICE_FILE, ORIGINAL_IMAGES_DIR
from src.transcript import TranscriptGenerator
from src.search_query import SearchQueryGenerator

VIDEO_URL = "https://api.pexels.com/videos/search"
PHOTO_URL = "https://api.pexels.com/v1/search"

MAX_RESULTS = 3
MAX_QUERIES_PER_SENTENCE = 5
REVIEW_JSON = Path("visual_review.json")
PLAN_JSON = Path("visual_review_plan.json")
APPROVED_JSON = Path("visual_review_approved.json")

session = requests.Session()
session.headers.update({"Authorization": PEXELS_API_KEY})

# Queries that are too generic to confidently call "almost OK".
GENERIC = {
    "hotel exterior",
    "hotel interior",
    "hotel guests travel",
    "travel destination",
    "hotel bedroom",
    "room interior",
    "hotel location city center",
    "hotel booking reservation",
    "hotel review",
    "hotel price booking value",
    "hotel amenities",
}

def concrete_score(query: str) -> int:
    q = query.lower().strip()
    if not q:
        return 0
    if q in GENERIC:
        return 0
    # Concrete visual nouns / activities.
    terms = {
        "birthday", "celebration", "family", "pet", "dog", "cat",
        "spa", "gym", "pool", "bed", "balcony", "bathroom", "wifi",
        "restaurant", "breakfast", "coffee", "kettle", "tv", "television",
        "parking", "airport", "beach", "ocean", "landmark", "museum",
        "temple", "church", "stadium", "golf", "tennis", "hiking", "cycling",
        "snorkeling", "diving", "kayaking", "surfing", "sailing",
        "boat", "suite", "courtyard", "garden", "sunset", "sunrise",
        "shopping", "playground", "meeting", "game room", "conference",
        "historic", "architecture", "attractions",
    }
    return sum(1 for t in terms if re.search(r"\b" + re.escape(t) + r"\b", q))

def pexels_search(query: str, kind: str = "videos", per_page: int = MAX_RESULTS):
    q = query.strip()
    if not q:
        return []
    url = VIDEO_URL if kind == "videos" else PHOTO_URL
    params = {"query": q, "per_page": per_page, "orientation": "landscape"}
    r = session.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("videos" if kind == "videos" else "photos", [])

def video_card(v: dict[str, Any]) -> dict[str, Any]:
    pictures = v.get("video_pictures") or []
    thumb = pictures[0].get("picture") if pictures else None
    files = [
        f for f in (v.get("video_files") or [])
        if f.get("link") and f.get("file_type") == "video/mp4"
    ]
    files.sort(key=lambda f: (f.get("width") or 0) * (f.get("height") or 0), reverse=True)
    return {
        "pexels_id": v.get("id"),
        "media_type": "video",
        "preview": thumb,
        "url": files[0].get("link") if files else None,
        "width": files[0].get("width") if files else None,
        "height": files[0].get("height") if files else None,
    }

def photo_card(p: dict[str, Any]) -> dict[str, Any]:
    src = p.get("src") or {}
    return {
        "pexels_id": p.get("id"),
        "media_type": "photo",
        "preview": src.get("medium") or src.get("large") or src.get("original"),
        "url": src.get("original") or src.get("large2x") or src.get("large"),
        "width": p.get("width"),
        "height": p.get("height"),
    }

def candidate_cards(query: str, kind: str = "videos"):
    if not PEXELS_API_KEY:
        raise RuntimeError("PEXELS_API_KEY is missing.")
    raw = pexels_search(query, kind, MAX_RESULTS)
    return [video_card(v) for v in raw] if kind == "videos" else [photo_card(p) for p in raw]

def status_for(query: str, cards: list[dict[str, Any]]) -> str:
    if concrete_score(query) <= 0 or not cards:
        return "INCOMPLETE"
    return "ALMOST OK"

def load_segments():
    if PLAN_JSON.exists():
        try:
            payload = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
            return payload.get("timeline_items", [])
        except Exception:
            pass

    # Exact plan generator; it reuses the real TimelineBuilder selection logic
    # but patches stock downloads into search-only placeholders.
    from review_plan import build_review_plan
    return build_review_plan()


def load_or_build():
    if PLAN_JSON.exists():
        try:
            payload = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
            return payload.get("timeline_items", [])
        except Exception:
            pass
    if REVIEW_JSON.exists():
        try:
            return json.loads(REVIEW_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return load_segments()

DATA = load_or_build()

# Cache remote searches in memory to minimize API calls.
SEARCH_CACHE: dict[tuple[str, str], list[dict[str, Any]]] = {}
INDEX_BY_KEY: dict[str, int] = {}

def refresh_index():
    INDEX_BY_KEY.clear()
    for n, item in enumerate(DATA):
        key = (
            f"{item.get('sentence_index', item.get('segment_index', 0)):03d} | "
            f"{item.get('visual_piece', item.get('piece', 1))} | "
            f"{item.get('review_status', item.get('status', 'INCOMPLETE'))} | "
            f"{item.get('query', '') or Path(str(item.get('media', ''))).name}"
        )
        INDEX_BY_KEY[key] = n

refresh_index()

def choices(include_all: bool):
    items = DATA if include_all else [x for x in DATA if x["status"] == "INCOMPLETE"]
    return [
        f"{x.get('sentence_index', x.get('segment_index', 0)):03d} | "
        f"{x.get('visual_piece', x.get('piece', 1))} | "
        f"{x.get('review_status', x.get('status', 'INCOMPLETE'))} | "
        f"{x.get('query', '') or Path(str(x.get('media', ''))).name}"
        for x in items
    ]

def get_item(choice):
    if not choice:
        return None
    if choice not in INDEX_BY_KEY:
        refresh_index()
    idx = INDEX_BY_KEY.get(choice)
    return DATA[idx] if idx is not None else None

def preview_md(item):
    if not item:
        return "No clip selected."
    return (
        f"**Segment:** {item.get('sentence_index', item.get('segment_index', 0)):03d} &nbsp; "
        f"**Piece:** {item.get('visual_piece', item.get('piece', 1))}  \n"
        f"**Time:** {float(item.get('start', 0)):.2f}s → {float(item.get('end', 0)):.2f}s  \n"
        f"**Status:** **{item.get('review_status', item.get('status', 'INCOMPLETE'))}**  \n"
        f"**Pexels ID:** {item.get('pexels_id') or 'n/a'}  \n\n"
        f"**Narration:** {item['text']}"
    )

def gallery_data(cards):
    return [(c.get("preview"), f"Pexels {c.get('pexels_id')}") for c in cards if c.get("preview")]

def on_select(choice):
    item = get_item(choice)
    if not item:
        return "", "", [], "No clip selected."
    cards = item.get("candidates") or []
    return item["text"], item["query"], gallery_data(cards), preview_md(item)

def do_search(choice, new_query, search_kind):
    item = get_item(choice)
    if not item:
        return [], "No clip selected.", "", ""
    query = str(new_query or "").strip()
    if not query:
        return [], "Query is empty.", item["query"], preview_md(item)

    key = (query.lower(), search_kind)
    if key not in SEARCH_CACHE:
        try:
            SEARCH_CACHE[key] = candidate_cards(query, search_kind)
        except Exception as exc:
            return [], f"Search failed: {exc}", query, preview_md(item)

    cards = SEARCH_CACHE[key]
    item["candidates"] = cards
    item["query"] = query
    item["media_type"] = "video" if search_kind == "videos" else "photo"
    item["status"] = status_for(query, cards)
    item["review_status"] = item["status"]
    if cards:
        item["pexels_id"] = cards[0]["pexels_id"]
        item["preview"] = cards[0]["preview"]
        item["edited"] = True
    else:
        item["pexels_id"] = None
        item["preview"] = None

    return gallery_data(cards), f"Status: {item['status']}", query, preview_md(item)

def save_current(choice):
    path = save_data(DATA)
    if PLAN_JSON.exists():
        PLAN_JSON.write_text(
            json.dumps({"version": 1, "timeline_items": DATA}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    return f"Saved: {path}"

def stats(include_all):
    shown = DATA if include_all else [x for x in DATA if x["status"] == "INCOMPLETE"]
    almost = sum(
        x.get("review_status", x.get("status", "INCOMPLETE")) == "ALMOST OK"
        for x in DATA
    )
    incomplete = sum(
        x.get("review_status", x.get("status", "INCOMPLETE")) == "INCOMPLETE"
        for x in DATA
    )
    return (
        f"Total query entries: {len(DATA)}  \n"
        f"✅ ALMOST OK: {almost}  \n"
        f"⚠ INCOMPLETE: {incomplete}  \n"
        f"Showing: {len(shown)}"
    )

def continue_download():
    """
    This is the ONLY action that downloads stock media.
    Review stage above does API search + remote thumbnail preview only.
    """
    media_root = Path("review_downloads")
    media_root.mkdir(parents=True, exist_ok=True)
    downloaded = []
    failures = []

    for n, item in enumerate(DATA):
        pid = item.get("pexels_id")
        if not pid:
            failures.append({"index": n, "reason": "No Pexels ID", "query": item.get("query")})
            continue

        url = None
        if item.get("candidates"):
            url = item["candidates"][0].get("url")

        if not url:
            try:
                cards = candidate_cards(item["query"], item.get("media_type", "video") + "s")
                if cards:
                    item["pexels_id"] = cards[0]["pexels_id"]
                    item["candidates"] = cards
                    url = cards[0].get("url")
            except Exception as exc:
                failures.append({"index": n, "reason": str(exc), "query": item.get("query")})
                continue

        if not url:
            failures.append({"index": n, "reason": "No downloadable Pexels URL", "query": item.get("query")})
            continue

        ext = ".mp4" if item.get("media_type") == "video" else ".jpg"
        out = media_root / f"{item['segment_index']:03d}_{item['piece']:02d}_{item['pexels_id']}{ext}"
        if not out.exists():
            try:
                r = session.get(url, stream=True, timeout=60)
                r.raise_for_status()
                with out.open("wb") as f:
                    for chunk in r.iter_content(1024 * 1024):
                        if chunk:
                            f.write(chunk)
            except Exception as exc:
                failures.append({"index": n, "reason": str(exc), "query": item.get("query")})
                continue

        item["downloaded_path"] = str(out)
        downloaded.append(str(out))

    save_data(DATA)
    return (
        f"Downloaded {len(downloaded)} stock assets.\n"
        f"Failures: {len(failures)}\n"
        f"Folder: {media_root.resolve()}",
        json.dumps({"items": DATA, "failures": failures}, indent=2, ensure_ascii=False),
    )

def result_choices(cards):
    return [
        f"{c.get('pexels_id')} | {c.get('media_type','video')} | "
        f"{c.get('width','?')}x{c.get('height','?')}"
        for c in cards
    ]

def selected_card(cards, choice):
    if not choice:
        return None
    pid = str(choice).split("|", 1)[0].strip()
    for c in cards:
        if str(c.get("pexels_id")) == pid:
            return c
    return None

with gr.Blocks(title="Hotel Visual Review") as demo:
    gr.Markdown("# Hotel Visual Review")
    gr.Markdown(
        "Review the exact generated timeline. Search/preview Pexels remotely. "
        "Nothing is downloaded until **Continue & Download**."
    )

    show_all = gr.Checkbox(label="Show ALMOST OK too", value=True)
    stats_box = gr.Markdown(stats(True))

    selector = gr.Dropdown(
        choices=choices(True),
        label="Timeline clips",
        value=None,
        allow_custom_value=False,
    )

    info = gr.Markdown("Select a timeline clip.")
    sentence = gr.Textbox(label="Narration", interactive=False, lines=4)
    query = gr.Textbox(label="Editable Pexels query")
    kind = gr.Radio(["videos", "photos"], value="videos", label="Search type")

    search_btn = gr.Button("Search Pexels", variant="primary")
    save_btn = gr.Button("Save this query")
    search_status = gr.Markdown()

    gallery = gr.Gallery(
        label="Pexels Preview",
        columns=3,
        rows=1,
        height="auto",
        object_fit="contain",
        allow_preview=True,
    )

    result_picker = gr.Radio(
        choices=[],
        label="Choose a Pexels result",
        visible=False,
    )
    use_btn = gr.Button("USE SELECTED PEXELS RESULT", visible=False, variant="primary")

    selected_preview = gr.Video(
        label="Selected Pexels video preview",
        visible=False,
        autoplay=False,
    )

    current_media = gr.Markdown("")

    continue_btn = gr.Button(
        "CONTINUE & DOWNLOAD STOCK MEDIA",
        variant="stop",
    )
    final_status = gr.Markdown()
    manifest_box = gr.Textbox(label="Download manifest / result", lines=12)

    def refresh_view(show):
        ch = choices(bool(show))
        # Always choose a valid first item or None.
        first = ch[0] if ch else None
        item = get_item(first) if first else None
        if not item:
            return (
                ch,
                stats(bool(show)),
                None,
                "",
                "",
                [],
                gr.update(visible=False, choices=[]),
                gr.update(visible=False),
                gr.update(visible=False, value=None),
                "No clips in this view.",
            )

        cards = item.get("candidates") or []
        return (
            ch,
            stats(bool(show)),
            first,
            item.get("text", ""),
            item.get("query", ""),
            gallery_data(cards),
            gr.update(
                visible=bool(cards),
                choices=result_choices(cards),
                value=(result_choices(cards)[0] if cards else None),
            ),
            gr.update(visible=bool(cards)),
            gr.update(
                visible=bool(cards),
                value=(cards[0].get("url") if cards else None),
            ),
            preview_md(item),
        )

    def choose_item(choice):
        item = get_item(choice)
        if not item:
            return (
                "", "", [], gr.update(visible=False, choices=[]),
                gr.update(visible=False), gr.update(visible=False, value=None),
                "No clip selected."
            )
        cards = item.get("candidates") or []
        labels = result_choices(cards)
        first_url = cards[0].get("url") if cards else None
        return (
            item.get("text", ""),
            item.get("query", ""),
            gallery_data(cards),
            gr.update(visible=bool(cards), choices=labels, value=(labels[0] if labels else None)),
            gr.update(visible=bool(cards)),
            gr.update(visible=bool(cards), value=first_url),
            preview_md(item),
        )

    def do_search_v2(choice, new_query, search_kind):
        item = get_item(choice)
        if not item:
            return (
                [], "No clip selected.", "", "No clip selected.",
                gr.update(visible=False, choices=[]),
                gr.update(visible=False),
                gr.update(visible=False, value=None),
            )
        q = str(new_query or "").strip()
        if not q:
            return (
                [], "Query is empty.", q, preview_md(item),
                gr.update(visible=False, choices=[]),
                gr.update(visible=False),
                gr.update(visible=False, value=None),
            )

        key = (q.lower(), search_kind)
        if key not in SEARCH_CACHE:
            try:
                SEARCH_CACHE[key] = candidate_cards(q, search_kind)
            except Exception as exc:
                return (
                    [], f"Search failed: {exc}", q, preview_md(item),
                    gr.update(visible=False, choices=[]),
                    gr.update(visible=False),
                    gr.update(visible=False, value=None),
                )

        cards = SEARCH_CACHE[key]
        item["candidates"] = cards
        item["query"] = q
        item["media_type"] = "video" if search_kind == "videos" else "photo"
        item["review_status"] = "ALMOST OK" if cards else "INCOMPLETE"

        labels = result_choices(cards)
        first_url = cards[0].get("url") if cards else None

        return (
            gallery_data(cards),
            f"Found {len(cards)} result(s). Status: **{item['review_status']}**",
            q,
            preview_md(item),
            gr.update(
                visible=bool(cards),
                choices=labels,
                value=(labels[0] if labels else None),
            ),
            gr.update(visible=bool(cards)),
            gr.update(visible=bool(cards), value=first_url),
        )

    def preview_result(result_choice, item_choice):
        item = get_item(item_choice)
        if not item:
            return gr.update(visible=False, value=None)
        card = selected_card(item.get("candidates") or [], result_choice)
        if not card:
            return gr.update(visible=False, value=None)
        if card.get("media_type") != "video" or not card.get("url"):
            return gr.update(visible=False, value=None)
        return gr.update(visible=True, value=card.get("url"))

    def use_selected_result(item_choice, result_choice):
        item = get_item(item_choice)
        if not item:
            return "No clip selected."

        card = selected_card(item.get("candidates") or [], result_choice)
        if not card:
            return "Select a Pexels result first."

        item["pexels_id"] = card.get("pexels_id")
        item["media_type"] = card.get("media_type")
        item["preview"] = card.get("preview")
        item["query"] = item.get("query", "")
        item["status"] = "ALMOST OK"
        item["review_status"] = "ALMOST OK"
        item["edited"] = True
        item["selected_url"] = card.get("url")
        return (
            f"Selected Pexels ID **{item['pexels_id']}**. "
            "Nothing is downloaded yet."
        )

    show_all.change(
        refresh_view,
        inputs=[show_all],
        outputs=[
            selector, stats_box, selector, sentence, query, gallery,
            result_picker, use_btn, selected_preview, info
        ],
    )

    selector.change(
        choose_item,
        inputs=[selector],
        outputs=[sentence, query, gallery, result_picker, use_btn, selected_preview, info],
    )

    search_btn.click(
        do_search_v2,
        inputs=[selector, query, kind],
        outputs=[
            gallery, search_status, query, info,
            result_picker, use_btn, selected_preview
        ],
    )

    result_picker.change(
        preview_result,
        inputs=[result_picker, selector],
        outputs=[selected_preview],
    )

    use_btn.click(
        use_selected_result,
        inputs=[selector, result_picker],
        outputs=[search_status],
    )

    save_btn.click(
        save_current,
        inputs=[selector],
        outputs=[final_status],
    )

    continue_btn.click(
        continue_download,
        outputs=[final_status, manifest_box],
    )


def launch_review():
    demo.launch(share=True)


if __name__ == "__main__":
    launch_review()
