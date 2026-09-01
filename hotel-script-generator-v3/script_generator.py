#!/usr/bin/env python3
"""
Hotel YouTube Script Generator V3
Designed for Kaggle GPU + Hugging Face Transformers.

V3 generates the script in separate sections so the model does not stop early.
Target: about 1,300-1,500 words / roughly 8-10 minutes.
"""

import json
import re
import argparse
from pathlib import Path

MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

SYSTEM_PROMPT = """
You write natural, simple English YouTube hotel-review narration.

STRICT FACT RULES:
- Use ONLY facts present in the supplied hotel JSON.
- Never invent amenities, restaurants, room views, facilities, distances, prices,
  policies, experiences, or hotel history.
- If data is missing, skip it.
- Never promote alcohol, bars, gambling, adult entertainment, or other prohibited
  content. Omit such facilities if they appear in the data.
- Prices must be described as the displayed price for the supplied stay dates,
  travelers, and room, never as a permanent price.
- Summarize reviews honestly. Do not exaggerate one review.
- Do not copy long review text word-for-word.
- Use conversational travel-video English.
- Avoid generic filler and repeated sentences.
- Do not claim the hotel is objectively the best.
- Do not mention JSON, scraping, extensions, automation, or the writing process.
- Return only narration for the requested section.
"""

SECTIONS = [
    ("INTRO", 90, 130, """Write a short engaging opening for this hotel review.
Introduce the hotel by name and location if available, mention the overall rating
if available, and tell viewers what the review will cover. Do not make unsupported
claims."""),
    ("OVERVIEW", 120, 160, """Explain what the hotel is, its property class, overall
guest rating and review count, and the strongest supported general impressions.
Use only the supplied data."""),
    ("LOCATION", 150, 200, """Explain the hotel's location and nearby landmarks,
attractions, transport points, and restaurants only when they are present in the
data. Include the supplied distances naturally. Do not invent anything."""),
    ("ROOMS", 190, 250, """Describe every useful room option in the supplied data.
Cover room size, sleeping capacity, bed type, room amenities, breakfast pricing
when available, cancellation information when available, and displayed prices
when available. Compare the options naturally without inventing differences."""),
    ("AMENITIES", 180, 240, """Explain the useful hotel amenities and facilities.
Organize them naturally: WiFi, air conditioning, housekeeping, room service,
business services, parking, laundry, accessibility, family facilities and other
supported amenities. Mention limitations such as no onsite parking when supported."""),
    ("DINING_AND_POLICIES", 170, 230, """Cover breakfast and restaurant availability
when supported, then practical policies such as check-in, check-out, minimum age,
pets, children, extra beds, cancellation, payment and other useful rules. Only
include facts actually present in the data."""),
    ("REVIEWS", 230, 300, """Give a balanced review summary. Start with the overall
rating and category scores when available. Summarize positive and negative guest
feedback, including specific issues only when supported. Do not turn one review
into a general claim. Explain what the review pattern suggests."""),
    ("VERDICT", 150, 200, """Give a balanced conclusion: who this hotel may suit,
what its main strengths are, what travelers should keep in mind, and a concise
final recommendation. Base every point on the supplied data. Finish naturally
for a YouTube video."""),
]

def clean_data(data):
    data = dict(data)

    rooms = data.get("rooms", [])
    seen = set()
    clean_rooms = []
    for r in rooms:
        key = (r.get("name"), r.get("size_sq_ft"), r.get("bed"),
               r.get("nightly_price"), r.get("total_price"))
        if key not in seen:
            seen.add(key)
            clean_rooms.append(r)
    data["rooms"] = clean_rooms

    reviews_obj = dict(data.get("reviews", {}))
    reviews = reviews_obj.get("guest_reviews", [])
    seen = set()
    clean_reviews = []
    for r in reviews:
        comment = re.sub(r"\s+", " ", str(r.get("comment", ""))).strip()
        # Drop obvious UI/text dumps rather than treating them as guest comments.
        bad = ("See all" in comment and "Room options" in comment) or (
            "Check availability" in comment and len(comment) > 180
        )
        if bad:
            continue
        key = (r.get("score"), comment)
        if key not in seen:
            seen.add(key)
            rr = dict(r)
            rr["comment"] = comment
            clean_reviews.append(rr)
    reviews_obj["guest_reviews"] = clean_reviews[:20]
    data["reviews"] = reviews_obj
    return data

def load_model():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=dtype, device_map="auto"
    )
    return tokenizer, model

def word_count(text):
    return len(re.findall(r"\b[\w'-]+\b", text))

def generate_section(tokenizer, model, data, title, min_words, max_words, task):
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    prompt = f"""
{SYSTEM_PROMPT}

SECTION: {title}
TARGET LENGTH: {min_words}-{max_words} words.

TASK:
{task}

Write this section as spoken narration. Stay close to the target length.
Use concrete facts from the data and add useful detail by explaining those facts,
not by inventing new information. Do not repeat information that belongs mainly
to another section.

HOTEL DATA:
{payload}
"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    # Allow enough tokens for the requested section.
    token_budget = max(420, int(max_words * 2.1))
    with __import__("torch").no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=token_budget,
            do_sample=True,
            temperature=0.65,
            top_p=0.9,
            repetition_penalty=1.08,
        )
    generated = out[0][inputs["input_ids"].shape[1]:]
    result = tokenizer.decode(generated, skip_special_tokens=True).strip()
    result = re.sub(r"^```(?:text|markdown)?\s*", "", result, flags=re.I)
    result = re.sub(r"\s*```$", "", result).strip()
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = clean_data(json.load(f))

    tokenizer, model = load_model()

    parts = []
    for title, min_words, max_words, task in SECTIONS:
        print(f"Generating {title} ({min_words}-{max_words} words)...")
        text = generate_section(tokenizer, model, data, title, min_words, max_words, task)
        print(f"  -> {word_count(text)} words")
        parts.append(text)

    script = "\n\n".join(parts)
    # Final cleanup: remove accidental section labels if the model adds them.
    script = re.sub(
        r"(?im)^\s*(INTRO|OVERVIEW|LOCATION|ROOMS|AMENITIES|DINING_AND_POLICIES|REVIEWS|VERDICT)\s*:?\s*$",
        "",
        script,
    )
    script = re.sub(r"\n{3,}", "\n\n", script).strip()

    Path(args.output).write_text(script, encoding="utf-8")
    words = word_count(script)
    print(f"Script saved: {args.output}")
    print(f"Word count: {words}")
    print(f"Approx narration: {words/150:.1f} minutes at 150 wpm")
    if words < 1250:
        print("WARNING: Still below 8-10 minutes; section generation can be expanded.")

if __name__ == "__main__":
    main()
