#!/usr/bin/env python3
import re
import argparse
from pathlib import Path

def clean_for_voice(text):
    # Basic symbols and typography
    text = text.replace("&", " and ")
    text = text.replace("WiFi", "Wi-Fi")
    text = text.replace("wifi", "Wi-Fi")
    text = text.replace("sq ft", "square feet")
    text = text.replace("sq. ft.", "square feet")
    text = text.replace("sqft", "square feet")

    # Scores and ratings: 8.4/10 -> 8 point 4 out of 10
    text = re.sub(
        r'(?<!\w)(\d+)\.(\d+)\s*/\s*10\b',
        r'\1 point \2 out of 10',
        text
    )
    # Decimal numbers: 4.2 -> 4 point 2
    text = re.sub(
        r'(?<![\w.])(\d+)\.(\d+)(?![\w.])',
        r'\1 point \2',
        text
    )

    # Fractions and percentages
    text = re.sub(r'(?<!\w)(\d+)\s*/\s*(\d+)(?!\w)', r'\1 out of \2', text)
    text = re.sub(r'(?<!\w)(\d+(?:\.\d+)?)\s*%', r'\1 percent', text)

    # Currency
    text = re.sub(r'\$\s*(\d+(?:\.\d+)?)', r'\1 US dollars', text)
    text = re.sub(r'\bUSD\s*(\d+(?:\.\d+)?)\b', r'\1 US dollars', text, flags=re.I)
    text = re.sub(r'\bINR\s*(\d+(?:\.\d+)?)\b', r'\1 Indian rupees', text, flags=re.I)
    text = re.sub(r'₹\s*(\d+(?:\.\d+)?)', r'\1 Indian rupees', text)

    # Common travel abbreviations
    replacements = {
        "min walk": "minute walk",
        "mins walk": "minutes walk",
        "min drive": "minute drive",
        "mins drive": "minutes drive",
        "AM": "AM",
        "PM": "PM",
    }
    for a, b in replacements.items():
        text = re.sub(r'\b' + re.escape(a) + r'\b', b, text, flags=re.I)

    # Time: 1:00 PM -> 1 PM; 11:30 AM remains natural
    text = re.sub(r'\b(\d{1,2}):00\s*(AM|PM)\b', r'\1 \2', text, flags=re.I)

    # Dates with numeric day/year are kept readable
    text = re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
                  r'\1 slash \2 slash \3', text)

    # Symbols that TTS may read awkwardly
    text = text.replace("+", " plus ")
    text = text.replace("=", " equals ")
    text = text.replace("–", "-").replace("—", "-")

    # Star ratings: 3-star -> three-star
    nums = {
        "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
        "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten"
    }
    def star(m):
        return nums.get(m.group(1), m.group(1)) + "-star"
    text = re.sub(r'\b([1-9]|10)-star\b', star, text, flags=re.I)

    # Clean excessive whitespace and punctuation
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' *([,.;!?]) *', r'\1 ', text)
    text = re.sub(r'\s+([,.;!?])', r'\1', text)
    text = re.sub(r' {2,}', ' ', text)

    # Give TTS clear paragraph pauses
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    src = Path(args.input).read_text(encoding="utf-8")
    cleaned = clean_for_voice(src)
    Path(args.output).write_text(cleaned, encoding="utf-8")

    print("Voice-ready script saved:", args.output)
    print("Original words:", len(src.split()))
    print("Voice-ready words:", len(cleaned.split()))

if __name__ == "__main__":
    main()
