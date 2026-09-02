import json
from pathlib import Path

import requests
import ipywidgets as W
from IPython.display import display, clear_output, Video as IPyVideo

try:
    from config import PEXELS_API_KEY
except Exception:
    PEXELS_API_KEY = ""

PLAN = Path("visual_review_plan.json")
STATE = Path("visual_review_edited.json")

def _load():
    if STATE.exists():
        try:
            data = json.loads(STATE.read_text(encoding="utf-8"))
            return data["timeline_items"] if isinstance(data, dict) else data
        except Exception:
            pass
    data = json.loads(PLAN.read_text(encoding="utf-8"))
    return data["timeline_items"] if isinstance(data, dict) else data

DATA = _load()
SEARCH_CACHE = {}
MEDIA_CACHE = {}

def _api_search(query, kind="videos", per_page=6):
    if not PEXELS_API_KEY:
        raise RuntimeError("PEXELS_API_KEY is missing in config.py")
    key = (query.strip().lower(), kind)
    if key in SEARCH_CACHE:
        return SEARCH_CACHE[key]

    url = (
        "https://api.pexels.com/videos/search"
        if kind == "videos"
        else "https://api.pexels.com/v1/search"
    )
    params = {
        "query": query,
        "per_page": per_page,
        "orientation": "landscape",
    }
    r = requests.get(
        url,
        headers={"Authorization": PEXELS_API_KEY},
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    rows = r.json().get("videos" if kind == "videos" else "photos", [])
    SEARCH_CACHE[key] = rows
    return rows

def _video_data(v):
    files = [
        f for f in (v.get("video_files") or [])
        if f.get("link") and f.get("file_type") == "video/mp4"
    ]
    # Prefer a sensible HD-ish file for final download, but preview remains remote.
    files.sort(
        key=lambda f: (f.get("width") or 0) * (f.get("height") or 0),
        reverse=True,
    )
    pic = v.get("video_pictures") or []
    thumb = pic[0].get("picture") if pic else None
    return {
        "pexels_id": v.get("id"),
        "type": "video",
        "thumb": thumb,
        "url": files[0]["link"] if files else None,
    }

def _photo_data(p):
    src = p.get("src") or {}
    return {
        "pexels_id": p.get("id"),
        "type": "photo",
        "thumb": src.get("medium") or src.get("large") or src.get("original"),
        "url": src.get("original") or src.get("large2x") or src.get("large"),
    }

def _results(query, kind):
    rows = _api_search(query, kind)
    return [_video_data(x) for x in rows] if kind == "videos" else [_photo_data(x) for x in rows]

def _save():
    STATE.write_text(
        json.dumps(
            {
                "version": 1,
                "timeline_items": DATA,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

def _status(item):
    if item.get("source_type") == "original":
        return "ALMOST OK"
    if item.get("pexels_id"):
        return item.get("review_status", "ALMOST OK")
    return "INCOMPLETE"

def launch():
    if not DATA:
        display(W.HTML("<b>No visual_review_plan.json found.</b>"))
        return

    title = W.HTML(
        "<h2 style='margin:0'>Hotel Visual Review — Direct Kaggle</h2>"
        "<p>Search/preview is remote. Nothing is downloaded during review.</p>"
    )

    idx = W.IntSlider(
        value=0,
        min=0,
        max=len(DATA)-1,
        step=1,
        description="Clip:",
        continuous_update=False,
        layout=W.Layout(width="650px"),
    )

    jump = W.IntText(value=0, description="Go to:", layout=W.Layout(width="180px"))
    show_only_incomplete = W.Checkbox(
        value=False,
        description="INCOMPLETE only",
    )
    stats = W.HTML()

    narration = W.Textarea(
        description="Narration:",
        disabled=True,
        layout=W.Layout(width="100%", height="110px"),
    )
    query = W.Text(
        description="Query:",
        layout=W.Layout(width="100%"),
    )
    kind = W.ToggleButtons(
        options=[("Videos", "videos"), ("Photos", "photos")],
        value="videos",
        description="Type:",
    )
    search = W.Button(description="Search Pexels", button_style="primary")
    use = W.Button(description="Use selected result", button_style="success")
    keep = W.Button(description="Keep current", button_style="")
    save = W.Button(description="Save review", button_style="info")
    download = W.Button(
        description="CONTINUE & DOWNLOAD STOCK MEDIA",
        button_style="warning",
        layout=W.Layout(width="100%"),
    )

    current = W.Output(layout={"border": "1px solid #ddd"})
    results = W.Output(layout={"border": "1px solid #ddd", "padding": "8px"})
    messages = W.Output()

    filtered = []

    def rebuild_filter():
        nonlocal filtered
        if show_only_incomplete.value:
            filtered = [
                i for i, x in enumerate(DATA)
                if _status(x) == "INCOMPLETE"
            ]
        else:
            filtered = list(range(len(DATA)))
        idx.max = max(0, len(filtered)-1) if filtered else 0
        idx.value = min(idx.value, idx.max)

    def actual_index():
        return filtered[idx.value] if filtered else 0

    def render_stats():
        almost = sum(_status(x) == "ALMOST OK" for x in DATA)
        incomplete = sum(_status(x) == "INCOMPLETE" for x in DATA)
        stats.value = (
            f"<b>Total:</b> {len(DATA)} &nbsp;&nbsp; "
            f"<b style='color:green'>✅ ALMOST OK: {almost}</b> &nbsp;&nbsp; "
            f"<b style='color:#b36b00'>⚠ INCOMPLETE: {incomplete}</b>"
        )

    def show_item(*_):
        n = actual_index()
        item = DATA[n]
        narration.value = item.get("text", "")
        query.value = item.get("query", "")
        q = item.get("query") or ""
        rid = item.get("pexels_id")
        source = item.get("source_type", "")
        status = _status(item)

        with current:
            clear_output(wait=True)
            display(W.HTML(
                f"<div style='font-size:14px;line-height:1.6'>"
                f"<b>Timeline item:</b> {n:03d}<br>"
                f"<b>Time:</b> {float(item.get('start',0)):.2f}s → "
                f"{float(item.get('end',0)):.2f}s<br>"
                f"<b>Piece:</b> {item.get('piece', item.get('visual_piece', 1))}<br>"
                f"<b>Status:</b> {status}<br>"
                f"<b>Source:</b> {source}<br>"
                f"<b>Pexels ID:</b> {rid or 'n/a'}<br>"
                f"<b>Query:</b> {q or '(none)'}"
                "</div>"
            ))
            media = item.get("preview")
            url = item.get("selected_url") or item.get("pexels_url")
            if media:
                display(W.Image(url=media, format="png", width=420))
            elif url and item.get("media_type") == "video":
                try:
                    # embed=False keeps the review stage download-free: the
                    # browser streams the direct Pexels MP4 URL.
                    display(IPyVideo(url=url, embed=False, width=560, html_attributes="controls"))
                except Exception as exc:
                    display(W.HTML(f"<b>Remote video preview unavailable:</b> {exc}"))

        render_stats()

    def do_search(_):
        n = actual_index()
        q = query.value.strip()
        if not q:
            return
        try:
            cards = _results(q, kind.value)
        except Exception as exc:
            with messages:
                clear_output(wait=True)
                print("Search error:", exc)
            return

        DATA[n]["candidates"] = cards
        DATA[n]["query"] = q
        DATA[n]["media_type"] = "video" if kind.value == "videos" else "photo"
        DATA[n]["review_status"] = "ALMOST OK" if cards else "INCOMPLETE"
        DATA[n]["status"] = DATA[n]["review_status"]

        with results:
            clear_output(wait=True)
            boxes = []
            for j, card in enumerate(cards):
                cap = W.HTML(
                    f"<b>Pexels {card['pexels_id']}</b><br>"
                    f"<button>Use</button>"
                )
                if card.get("thumb"):
                    try:
                        img = W.Image(
                            value=requests.get(card["thumb"], timeout=20).content,
                            format="png",
                            width=250,
                            height=140,
                        )
                    except Exception:
                        img = W.HTML(
                            f"<img src='{card['thumb']}' "
                            "style='width:250px;height:140px;object-fit:cover'>"
                        )
                else:
                    img = W.HTML("<div style='width:250px;height:140px'>No thumbnail</div>")
                pick = W.Button(
                    description=f"Use {j+1}",
                    layout=W.Layout(width="250px")
                )

                def choose(_, n=n, card=card):
                    DATA[n]["pexels_id"] = card["pexels_id"]
                    DATA[n]["selected_url"] = card.get("url")
                    DATA[n]["preview"] = card.get("thumb")
                    DATA[n]["media_type"] = card.get("type")
                    DATA[n]["query"] = query.value.strip()
                    DATA[n]["review_status"] = "ALMOST OK"
                    DATA[n]["status"] = "ALMOST OK"
                    with messages:
                        clear_output(wait=True)
                        print(
                            f"Selected Pexels ID {card['pexels_id']} "
                            f"for timeline item {n:03d}. Nothing downloaded."
                        )
                    show_item()

                pick.on_click(choose)
                boxes.append(W.VBox([img, cap, pick]))
            if boxes:
                display(W.HBox(boxes))
            else:
                display(W.HTML("No Pexels results found."))

        with messages:
            clear_output(wait=True)
            print(f"Found {len(cards)} result(s) for: {q}")

        render_stats()
        show_item()

    def keep_current(_):
        with messages:
            clear_output(wait=True)
            print(f"Keeping current media for timeline item {actual_index():03d}.")
        show_item()

    def save_now(_):
        _save()
        with messages:
            clear_output(wait=True)
            print(f"Saved review: {STATE.resolve()}")

    def download_now(_):
        # Download approved stock files only now.
        root = Path("review_downloads")
        root.mkdir(exist_ok=True)
        failures = []
        count = 0

        for n, item in enumerate(DATA):
            if item.get("source_type") == "original":
                continue
            pid = item.get("pexels_id")
            if not pid:
                failures.append((n, "missing Pexels ID"))
                continue

            kind2 = item.get("media_type", "video")
            try:
                cards = item.get("candidates") or _results(
                    item.get("query", ""), "videos" if kind2 == "video" else "photos"
                )
                selected = next(
                    (c for c in cards if str(c.get("pexels_id")) == str(pid)),
                    None,
                )
                if not selected:
                    failures.append((n, f"Pexels ID {pid} not found"))
                    continue

                url = selected.get("url")
                if not url:
                    failures.append((n, f"Pexels ID {pid} has no URL"))
                    continue

                ext = ".mp4" if kind2 == "video" else ".jpg"
                out = root / f"{n:03d}_{pid}{ext}"
                if not out.exists():
                    rr = requests.get(url, stream=True, timeout=90)
                    rr.raise_for_status()
                    with out.open("wb") as f:
                        for chunk in rr.iter_content(1024 * 1024):
                            if chunk:
                                f.write(chunk)

                item["downloaded_path"] = str(out)
                count += 1

            except Exception as exc:
                failures.append((n, str(exc)))

        _save()
        with messages:
            clear_output(wait=True)
            print(f"Downloaded: {count}")
            print(f"Failures: {len(failures)}")
            if failures:
                print("First failures:", failures[:10])
            print(f"Folder: {root.resolve()}")

    def on_filter(_):
        rebuild_filter()
        show_item()

    idx.observe(show_item, names="value")
    show_only_incomplete.observe(on_filter, names="value")
    jump.observe(
        lambda change: (
            setattr(idx, "value", max(0, min(idx.max, int(change["new"]))))
            if change["new"] is not None else None
        ),
        names="value",
    )
    search.on_click(do_search)
    keep.on_click(keep_current)
    save.on_click(save_now)
    download.on_click(download_now)

    rebuild_filter()
    show_item()

    display(
        W.VBox([
            title,
            W.HBox([show_only_incomplete, stats]),
            W.HBox([idx, jump]),
            W.HTML("<hr>"),
            current,
            narration,
            query,
            kind,
            W.HBox([search, keep, save]),
            results,
            messages,
            download,
        ])
    )
