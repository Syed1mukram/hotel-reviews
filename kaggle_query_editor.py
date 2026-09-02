import json
from pathlib import Path
import re
import requests
import ipywidgets as W
from IPython.display import display, clear_output

PLAN = Path("visual_review_plan.json")
STATE = Path("visual_review_queries.json")

try:
    from config import PEXELS_API_KEY
except Exception:
    PEXELS_API_KEY = ""

def load_data():
    source = STATE if STATE.exists() else PLAN
    payload = json.loads(source.read_text(encoding="utf-8"))
    return payload.get("timeline_items", payload)

DATA = load_data()

def save_data():
    STATE.write_text(
        json.dumps(
            {"version": 1, "timeline_items": DATA},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

def extract_queries(item):
    q = str(item.get("query") or "").strip()
    return [x.strip() for x in q.split("||") if x.strip()]

def set_queries(item, queries):
    item["query"] = " || ".join(q.strip() for q in queries if q.strip())

def launch():
    if not DATA:
        display(W.HTML("<b>No visual_review_plan.json found.</b>"))
        return

    title = W.HTML(
        "<h2 style='margin:0'>Hotel Review — Search Query Editor</h2>"
        "<p>Edit only the Pexels search queries. Nothing downloads while editing.</p>"
    )

    segment = W.IntSlider(
        value=0,
        min=0,
        max=len(DATA)-1,
        step=1,
        description="Item:",
        continuous_update=False,
        layout=W.Layout(width="650px"),
    )

    text_box = W.Textarea(
        description="TEXT:",
        disabled=True,
        layout=W.Layout(width="100%", height="110px"),
    )

    queries_box = W.Textarea(
        description="SEARCH:",
        layout=W.Layout(width="100%", height="120px"),
        placeholder="One query per line",
    )

    info = W.HTML()
    save_btn = W.Button(description="SAVE QUERY", button_style="success")
    next_btn = W.Button(description="NEXT", button_style="primary")
    prev_btn = W.Button(description="PREVIOUS")
    finish_btn = W.Button(
        description="SAVE & CONTINUE TO DOWNLOAD",
        button_style="warning",
        layout=W.Layout(width="100%"),
    )

    output = W.Output()

    def show():
        item = DATA[segment.value]
        text_box.value = str(item.get("text", ""))
        queries = extract_queries(item)

        # Show each existing query on its own editable line.
        queries_box.value = "\n".join(queries) if queries else ""

        start = float(item.get("start", 0))
        end = float(item.get("end", 0))
        info.value = (
            f"<b>[{segment.value:03d}]</b> "
            f"{start:.2f} → {end:.2f} &nbsp; "
            f"<b>Queries:</b> {len(queries)}"
        )

    def save_current():
        lines = [
            re.sub(r"\s+", " ", line.strip())
            for line in queries_box.value.splitlines()
            if line.strip()
        ]
        set_queries(DATA[segment.value], lines)
        save_data()
        with output:
            clear_output(wait=True)
            print(f"Saved item {segment.value:03d}:")
            for i, q in enumerate(lines, 1):
                print(f"  [SEARCH QUERY {i}] {q}")

    def save_click(_):
        save_current()

    def next_click(_):
        save_current()
        if segment.value < segment.max:
            segment.value += 1

    def prev_click(_):
        save_current()
        if segment.value > segment.min:
            segment.value -= 1

    def finish(_):
        save_current()
        with output:
            clear_output(wait=True)
            print("========================================")
            print("QUERY REVIEW COMPLETE")
            print(f"Saved: {STATE.resolve()}")
            print(f"Timeline items: {len(DATA)}")
            print("No stock media was downloaded during editing.")
            print("========================================")
            print("Next step: run the download/final-render stage using this file.")

    segment.observe(lambda change: show(), names="value")
    save_btn.on_click(save_click)
    next_btn.on_click(next_click)
    prev_btn.on_click(prev_click)
    finish_btn.on_click(finish)

    show()

    display(
        W.VBox([
            title,
            info,
            segment,
            text_box,
            queries_box,
            W.HBox([prev_btn, save_btn, next_btn]),
            finish_btn,
            output,
        ])
    )
