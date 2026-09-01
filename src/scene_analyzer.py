import re


VISUAL_CATEGORIES = {

    "room": [
        "room",
        "suite",
        "bedroom",
        "bed",
        "villa",
        "apartment",
        "family room",
        "deluxe",
        "king",
        "queen",
    ],

    "bathroom": [
        "bathroom",
        "shower",
        "bathtub",
        "washroom",
        "toilet",
    ],

    "pool": [
        "pool",
        "swimming",
        "infinity pool",
        "lazy river",
        "water park",
    ],

    "beach": [
        "beach",
        "ocean",
        "sea",
        "shore",
        "coast",
        "sand",
        "waves",
    ],

    "balcony": [
        "balcony",
        "terrace",
        "ocean view",
        "sea view",
        "mountain view",
        "view",
    ],

    "restaurant": [
        "restaurant",
        "buffet",
        "breakfast",
        "dining",
        "food",
        "chef",
        "meal",
    ],

    "bar": [
        "bar",
        "cocktail",
        "lounge",
        "drinks",
        "nightlife",
    ],

    "spa": [
        "spa",
        "massage",
        "wellness",
        "sauna",
        "treatment",
    ],

    "gym": [
        "gym",
        "fitness",
        "workout",
        "exercise",
    ],

    "lobby": [
        "lobby",
        "reception",
        "check in",
        "check-in",
        "entrance",
        "front desk",
    ],

    "kids": [
        "kids club",
        "children",
        "playground",
        "kids",
        "family activities",
    ],

    "outside": [
        "resort",
        "hotel",
        "building",
        "exterior",
        "garden",
        "aerial",
        "drone",
        "entrance",
        "grounds",
        "property",
    ],

}


class SceneAnalyzer:

    def __init__(self):
        pass

    # -----------------------------------------------------

    def analyze(self, text):

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9\s-]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        found = []

        scene = "general"

        # Check longer phrases first
        categories = {}

        for category, words in VISUAL_CATEGORIES.items():

            categories[category] = sorted(
                words,
                key=len,
                reverse=True
            )

        for category, words in categories.items():

            for word in words:

                if word in text:

                    if word not in found:
                        found.append(word)

                    if scene == "general":
                        scene = category

        # -------------------------------------------------
        # No specific category
        # -------------------------------------------------

        if not found:

            return {
                "scene": "general",
                "prompt": text,
                "keywords": [],
            }

        # -------------------------------------------------
        # Build visual search prompt
        # -------------------------------------------------

        prompt_parts = []

        for keyword in found:

            if keyword not in prompt_parts:
                prompt_parts.append(keyword)

        prompt = ", ".join(prompt_parts)

        return {
            "scene": scene,
            "prompt": prompt,
            "keywords": found,
        }


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    analyzer = SceneAnalyzer()

    while True:

        text = input("Text : ").strip()

        if not text:
            break

        result = analyzer.analyze(text)

        print(result)