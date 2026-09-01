import re
from pathlib import Path
from collections import deque

from moviepy.audio.io.AudioFileClip import AudioFileClip

from src.transcript import TranscriptGenerator
from src.scene_analyzer import SceneAnalyzer
from src.image_matcher import ImageMatcher
from src.pexels_api import PexelsAPI
from src.search_query import SearchQueryGenerator


class TimelineBuilder:

    def __init__(
        self,
        audio_file,
        images_dir,
    ):

        self.stock_image_topics = [
            "breakfast food",
            "restaurant food",
            "happy family vacation",
            "tourists exploring",
            "tropical beach",
            "ocean beach",
            "mountain landscape",
            "tropical nature",
            "sunset landscape",
            "travelers walking",
            "boat island",
            "local street",
            "travel activity",
            "swimming",
        ]

        self.audio_file = Path(
            audio_file
        )

        self.images_dir = Path(
            images_dir
        )

        self.transcript = (
            TranscriptGenerator()
        )

        self.scene = (
            SceneAnalyzer()
        )

        self.matcher = (
            ImageMatcher()
        )

        self.pexels = (
            PexelsAPI()
        )

        self.query_generator = (
            SearchQueryGenerator()
        )

        # Every visual used in this video
        self.used_visuals = set()

        # Last visual source types
        self.recent_visuals = deque(
            maxlen=4
        )

        # Counters
        self.stock_image_count = 0
        self.stock_video_count = 0
        self.visual_count = 0

        # Target approximately 15% stock images.
        # Selection is based on visual_count and remains separate
        # from original hotel images and GPU rendering.
        self.stock_image_target_ratio = 0.15

        # Minimum acceptable match score for an "original" hotel image.
        # Below this, the match is too weak/generic to trust — fall
        # back to stock instead of forcing an unrelated original photo.
        self.min_original_score = 0.22

    # =========================================================
    # ORIGINAL IMAGE
    # =========================================================

    def find_first_original(
        self,
        text,
        scene,
    ):
        """Force the first visual to be an unused original hotel image."""
        result = self.matcher.find_best(
            prompt=text,
            scene=scene,
        )

        if not result:
            result = self.matcher.find_best(
                prompt="hotel exterior hotel resort",
                scene="outside",
            )

        if not result:
            return None

        image_path, score = result
        image_path = Path(image_path)
        key = str(image_path.resolve())

        if key in self.used_visuals:
            return None

        self.used_visuals.add(key)
        self.recent_visuals.append("original")

        return {
            "media": image_path,
            "media_type": "image",
            "source_type": "original",
            "label": None,
            "score": score,
        }

    def find_original(
        self,
        text,
        scene,
    ):

        result = self.matcher.find_best(
            prompt=text,
            scene=scene,
        )

        if not result:
            return None

        image_path, score = result

        # Reject weak matches: better to fall back to a relevant
        # stock clip than force an unrelated original hotel photo.
        if score is not None and score < self.min_original_score:
            return None

        image_path = Path(
            image_path
        )

        key = str(
            image_path.resolve()
        )

        if key in self.used_visuals:
            return None

        self.used_visuals.add(
            key
        )

        self.recent_visuals.append(
            "original"
        )

        return {
            "media": image_path,
            "media_type": "image",
            "source_type": "original",
            "label": None,
            "score": score,
        }

    # =========================================================
    # STOCK VIDEO
    # =========================================================

    def find_stock_video(
        self,
        query,
    ):

        video = self.pexels.download(
            query
        )

        if video is None:
            return None

        video = Path(
            video
        )

        key = str(
            video.resolve()
        )

        if key in self.used_visuals:
            return None

        self.used_visuals.add(
            key
        )

        self.recent_visuals.append(
            "stock_video"
        )

        return {
            "media": video,
            "media_type": "video",
            "source_type": "stock_video",
            "label": "STOCK VIDEO",
            "score": None,
        }

    # =========================================================
    # STOCK IMAGE
    # =========================================================

    def find_stock_image(
        self,
        query,
    ):

        if self.visual_count > 0:
            target_images = max(
                1,
                int(
                    self.visual_count
                    * self.stock_image_target_ratio
                )
            )

            if self.stock_image_count >= target_images:
                return None

        # Use the sentence-derived query directly.
        stock_query = query.strip()

        if not stock_query:
            return None

        print(
            f"[STOCK IMAGE QUERY] "
            f"{stock_query}"
        )

        image = self.pexels.download_image(
            stock_query
        )

        if image is None:
            return None

        image = Path(image)

        key = str(
            image.resolve()
        )

        if key in self.used_visuals:
            return None

        self.used_visuals.add(
            key
        )

        self.recent_visuals.append(
            "stock_image"
        )

        self.stock_image_count += 1

        return {
            "media": image,
            "media_type": "image",
            "source_type": "stock_image",
            "label": "STOCK IMAGE",
            "score": None,
        }

    # =========================================================
    # TWO ORIGINALS CHECK
    # =========================================================

    def should_prefer_stock(self):

        if len(
            self.recent_visuals
        ) < 2:

            return False

        last_two = list(
            self.recent_visuals
        )[-2:]

        return (
            last_two[0] == "original"
            and
            last_two[1] == "original"
        )

    # =========================================================
    # STOCK IMAGE OPPORTUNITY
    # =========================================================

    def should_try_stock_image(self):

        if self.visual_count <= 0:
            return False

        target_images = max(
            1,
            int(
                self.visual_count
                * self.stock_image_target_ratio
            )
        )

        # Only request an image when the current count is
        # below the approximate 15% target.
        return (
            self.stock_image_count
            < target_images
        )

    # =========================================================
    # STRICT SENTENCE VISUAL QUERY
    # =========================================================

    def build_visual_query(self, text, scene):
        """Build a concise visual query from the actual sentence."""
        original = str(text).strip()
        t = re.sub(r"[^a-z0-9]+", " ", original.lower()).strip()

        # Explicit named/semantic concepts. More specific concepts win.
        rules = [
            ("wifi", ["wi fi", "wifi", "wireless internet"]),
            ("air conditioning", ["air conditioning", "air conditioner", "air conditioned"]),
            ("mini fridge", ["mini fridge", "mini bar", "minibar", "refrigerator"]),
            ("coffee maker", ["coffee maker", "coffee machine", "kettle", "electric kettle"]),
            ("hotel bathroom", ["bathroom", "shower", "bathtub", "toiletries", "shampoo", "soap", "towels"]),
            ("hotel bed", ["king bed", "queen bed", "twin bed", "twin beds", "bunk bed", "bed", "beds"]),
            ("breakfast", ["breakfast", "buffet"]),
            ("hotel restaurant dining", ["restaurant", "restaurants", "dining", "dinner", "lunch", "meal", "culinary", "coffee shop", "cafe"]),
            ("room service", ["room service", "in room dining", "inroom dining"]),
            ("housekeeping", ["housekeeping", "cleanliness", "cleaning", "spotless"]),
            ("hotel staff", ["staff", "hospitality", "concierge", "receptionist", "service"]),
            ("parking", ["parking", "car park", "parking lot"]),
            ("electric vehicle charging station", ["electric car charging", "ev charging", "charging station"]),
            ("airport", ["airport"]),
            ("transportation", ["transportation", "transport", "taxi", "shuttle", "transit center", "station"]),
            ("museum", ["museum", "archaeological museum"]),
            ("temple", ["temple", "temples"]),
            ("stadium", ["stadium"]),
            ("landmark attractions", ["attraction", "attractions", "landmark", "sightseeing", "cultural center", "art center", "theater", "theatre"]),
            ("swimming pool", ["swimming pool", "pool", "poolside"]),
            ("gym", ["gym", "fitness center", "fitness centre", "workout"]),
            ("spa", ["spa", "wellness", "massage", "treatment"]),
            ("game room", ["game room", "games room"]),
            ("meeting room", ["meeting room", "business center", "business centre", "conference"]),
            ("family vacation", ["family", "families", "kids", "children"]),
            ("hotel balcony", ["balcony", "terrace", "patio", "veranda"]),
            ("hotel courtyard", ["courtyard", "palm lined courtyard"]),
            ("beach", ["beach", "beaches", "beachfront", "ocean", "sea", "coast", "shore"]),
            ("island", ["island", "islands"]),
            ("nature", ["nature", "jungle", "forest", "waterfall", "wildlife"]),
            ("snorkeling", ["snorkeling", "snorkelling"]),
            ("diving", ["scuba diving", "diving"]),
            ("kayaking", ["kayaking", "kayak"]),
            ("surfing", ["surfing", "surf"]),
            ("hiking", ["hiking", "hike", "trekking"]),
            ("cycling", ["cycling", "bicycle", "biking"]),
            ("golf", ["golf", "golf course"]),
            ("tennis", ["tennis"]),
            ("water sports", ["water sports", "watersports"]),
            ("check in reception", ["check in", "checkin", "arrival", "front desk"]),
            ("check out departure", ["check out", "checkout", "departure"]),
            ("hotel price", ["price", "cost", "per night", "budget", "affordable", "fees", "taxes"]),
            ("hotel reviews", ["review", "reviews", "rating", "ratings", "score", "guest"]),
        ]

        negative_parking = any(
            phrase in t for phrase in [
                "no parking", "no parking space", "no parking spaces",
                "parking unavailable", "does not offer parking",
                "doesnt offer parking", "without parking"
            ]
        )

        found = []
        for label, words in rules:
            if any(word in t for word in words):
                if label == "parking" and negative_parking:
                    continue
                if label not in found:
                    found.append(label)

        # Negative parking still needs a relevant visual, but not a
        # positive "hotel parking" search.
        if negative_parking:
            return "empty street parking roadside access"

        if found:
            # Keep the query compact. Multiple concepts are intentionally
            # combined when they occur in the same sentence.
            return " ".join(found[:3])

        # Preserve useful nouns from the sentence for places/brands.
        # This is deliberately conservative; filler words are excluded.
        stop = {
            "the", "a", "an", "and", "or", "but", "so", "to", "of", "in",
            "on", "at", "for", "with", "from", "by", "as", "is", "are",
            "was", "were", "be", "been", "being", "this", "that", "these",
            "those", "it", "its", "they", "their", "them", "there", "here",
            "just", "also", "very", "quite", "really", "now", "then",
            "some", "many", "most", "more", "less", "only", "about",
            "around", "roughly", "nearly", "even", "still", "back",
            "well", "like", "one", "two", "three", "four", "five",
            "minute", "minutes", "night", "per", "day", "today", "tomorrow",
            "will", "would", "could", "should", "can", "may", "might",
            "you", "your", "we", "our", "they", "their", "guest", "guests",
        }

        words = re.findall(r"[a-z0-9]+", t)
        useful = []
        for word in words:
            if len(word) < 3 or word in stop:
                continue
            if word.isdigit():
                continue
            if word not in useful:
                useful.append(word)

        # Don't turn generic prose into a bad Pexels query.
        if useful:
            return " ".join(useful[:5])

        scene_text = str(scene).lower()
        defaults = [
            ("room", "hotel room interior"),
            ("amenit", "hotel amenities"),
            ("dining", "hotel restaurant dining"),
            ("location", "hotel location city center"),
            ("review", "hotel review"),
            ("policy", "hotel reception"),
            ("intro", "hotel exterior"),
            ("outside", "hotel exterior"),
        ]

        for key, value in defaults:
            if key in scene_text:
                return value

        # Safe hotel-specific fallback instead of "travel destination".
        return "hotel interior"


    def _visual_result_is_new(self, result):
        if not result:
            return False
        media = result.get("media")
        if not media:
            return False
        key = str(Path(media).resolve())
        if key in self.used_visuals:
            return False
        self.used_visuals.add(key)
        return True

    # =========================================================
    # VISUAL SELECTION
    # =========================================================

    def select_visuals(self, text, is_first=False, context_before="", context_after=""):
        """Select up to 4 visual concepts while keeping the transcript sentence intact."""
        scene = self.scene.analyze(text)["scene"]

        prompt = self.query_generator.generate(
            text=str(text),
            scene=str(scene),
        )

        # Use neighboring sentences only when the current one is vague.
        if prompt.startswith("travel destination") and (context_before or context_after):
            merged = f"{context_before} {text} {context_after}".strip()
            better = self.query_generator.generate(text=merged, scene=str(scene))
            if better and not better.startswith("travel destination"):
                prompt = better

        text_l = str(text).lower()
        concept_rules = [
            (("pool", "swimming pool", "poolside"), "hotel swimming pool"),
            (("spa", "wellness", "massage"), "hotel spa wellness"),
            (("gym", "fitness center", "fitness centre"), "hotel gym fitness"),
            (("wifi", "wi-fi", "wireless internet"), "hotel wifi"),
            (("air conditioning", "air conditioner", "air-conditioned"), "hotel air conditioning"),
            (("mini fridge", "mini-fridge", "minibar", "refrigerator"), "hotel room mini fridge"),
            (("balcony", "terrace", "patio", "veranda"), "hotel balcony terrace"),
            (("bathroom", "shower", "bathtub", "toiletries"), "hotel bathroom"),
            (("breakfast", "breakfast buffet"), "hotel breakfast buffet"),
            (("restaurant", "dining", "dinner", "lunch", "cafe"), "hotel restaurant dining"),
            (("room service",), "hotel room service"),
            (("king bed", "queen bed", "twin bed", "bunk bed", "bedroom"), "hotel bedroom bed"),
            (("beach", "ocean", "sea", "coast"), "beach ocean"),
            (("airport",), "airport travel"),
            (("museum",), "museum"),
            (("temple",), "temple landmark"),
            (("landmark", "attraction", "sightseeing"), "city landmark travel"),
        ]

        concepts = []
        for triggers, query in concept_rules:
            if any(t in text_l for t in triggers) and query not in concepts:
                concepts.append(query)

        # For ordinary one-concept sentences, keep the generator's better query.
        if len(concepts) <= 1:
            concepts = [prompt or "hotel interior"]

        # Cap at 4 visual pieces.
        results = []
        for idx, concept in enumerate(concepts[:4]):
            print(f"[SEARCH QUERY] {concept}")
            self.visual_count += 1

            if is_first and idx == 0:
                result = self.find_first_original(text=text, scene=scene)
                if result:
                    results.append(result)
                    continue

            result = self.find_original(text=concept, scene=scene)
            if result:
                results.append(result)
                continue

            if self.should_try_stock_image():
                print("[MIX] Trying relevant stock image...")
                result = self.find_stock_image(query=concept)
                if result:
                    results.append(result)
                    continue

            result = self.find_stock_video(query=concept)
            if result:
                self.stock_video_count += 1
                results.append(result)
                continue

            result = self.find_stock_image(query=concept)
            if result:
                results.append(result)

        return results

    def select_visual(self, text, is_first=False, context_before="", context_after=""):
        visuals = self.select_visuals(
            text=text,
            is_first=is_first,
            context_before=context_before,
            context_after=context_after,
        )
        return visuals[0] if visuals else None

    # =========================================================
    # BUILD TIMELINE
    # =========================================================

    def build(self):

        print(
            "\n========================================"
        )

        print(
            "Generating hotel review timeline"
        )

        print(
            "========================================"
        )

        # -----------------------------------------------------
        # TRANSCRIPT
        # -----------------------------------------------------

        segments = (
            self.transcript.transcribe(
                self.audio_file
            )
        )

        if not segments:

            raise RuntimeError(
                "No transcript segments found."
            )

        # -----------------------------------------------------
        # ORIGINAL IMAGES
        # -----------------------------------------------------

        print(
            "\n[INFO] Indexing original hotel images..."
        )

        self.matcher.index_images(
            self.images_dir
        )

        # -----------------------------------------------------
        # AUDIO DURATION
        # -----------------------------------------------------

        with AudioFileClip(
            str(self.audio_file)
        ) as audio:

            audio_duration = float(
                audio.duration
            )

        timeline = []

        # -----------------------------------------------------
        # VISUAL TIMELINE
        # -----------------------------------------------------

        # Keep transcript/audio order unchanged. Only the explicit intro
        # segment receives first-visual priority.
        intro_index = None

        for idx, segment in enumerate(segments):
            segment_text = str(
                segment.get("text", "")
            ).strip().lower()

            if (
                segment_text == "intro"
                or segment_text.startswith("intro:")
                or segment_text.startswith("[intro]")
            ):
                intro_index = idx
                break

        for position, (i, segment) in enumerate(
            enumerate(segments)
        ):

            if i == 0:

                start = 0.0

            else:

                start = float(
                    segments[i - 1]["end"]
                )

            if i < len(
                segments
            ) - 1:

                end = float(
                    segments[i]["end"]
                )

            else:

                end = audio_duration

            if end <= start:
                continue

            duration = (
                end - start
            )

            text = segment[
                "text"
            ].strip()

            if not text:
                continue

            print(
                f"\n[{i:03d}] "
                f"{start:.2f} -> "
                f"{end:.2f}"
            )

            print(
                f"TEXT: {text}"
            )

            visuals = self.select_visuals(
                text,
                is_first=(i == 0 if intro_index is None else i == intro_index),
                context_before=(
                    segments[i - 1]["text"]
                    if i > 0 else ""
                ),
                context_after=(
                    segments[i + 1]["text"]
                    if i < len(segments) - 1 else ""
                ),
            )

            if not visuals:
                continue

            # Keep the transcript sentence intact. Multiple selected visuals
            # simply share the sentence's original duration.
            piece_duration = duration / len(visuals)

            for piece_index, visual in enumerate(visuals):
                piece_start = start + piece_index * piece_duration
                piece_end = (
                    end
                    if piece_index == len(visuals) - 1
                    else piece_start + piece_duration
                )

                timeline.append({
                    "start": piece_start,
                    "end": piece_end,
                    "duration": piece_end - piece_start,
                    "text": text,
                    "media": visual["media"],
                    "media_type": visual["media_type"],
                    "source_type": visual["source_type"],
                    "label": visual["label"],
                    "score": visual["score"],
                    "sentence_index": i,
                    "visual_piece": piece_index + 1,
                    "visual_pieces_total": len(visuals),
                })

                print(f"SOURCE: {visual['source_type']}")
                print(f"MEDIA: {Path(visual['media']).name}")

        # -----------------------------------------------------
        # DEBUG
        # -----------------------------------------------------

        print(
            "\n========================================"
        )

        print(
            f"Segments : {len(segments)}"
        )

        print(
            f"Timeline : {len(timeline)}"
        )

        print(
            f"Audio    : "
            f"{audio_duration:.3f} sec"
        )

        print(
            f"Stock Images Used : "
            f"{self.stock_image_count}"
        )

        print(
            f"Stock Videos Used : "
            f"{self.stock_video_count}"
        )

        print(
            "========================================"
        )

        total = 0.0

        for i, item in enumerate(
            timeline
        ):

            total += float(
                item["duration"]
            )

            print(
                f"{i:03d} | "
                f"{item['start']:.3f} -> "
                f"{item['end']:.3f} | "
                f"{item['duration']:.3f} | "
                f"{item['source_type']} | "
                f"{Path(item['media']).name}"
            )

        print(
            "----------------------------------------"
        )

        print(
            f"Timeline Total : "
            f"{total:.3f} sec"
        )

        print(
            f"Audio Duration : "
            f"{audio_duration:.3f} sec"
        )

        print(
            "========================================"
        )

        return timeline