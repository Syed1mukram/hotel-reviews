from pathlib import Path
from collections import deque
import re

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
        """Build a focused Pexels/image-search query from sentence meaning."""
        t = re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()

        concepts = [
            ("wifi", ["wi fi", "wifi", "wireless internet"]),
            ("air conditioning", ["air conditioning", "air conditioner", "air conditioned"]),
            ("mini fridge", ["mini fridge", "mini bar", "minibar", "refrigerator"]),
            ("hotel bathroom", ["bathroom", "shower", "bathtub", "toiletries"]),
            ("hotel bed", ["bed", "beds", "mattress", "sleep"]),
            ("breakfast", ["breakfast", "breakfast buffet"]),
            ("hotel restaurant", ["restaurant", "dining", "dinner", "lunch", "meal"]),
            ("room service", ["room service", "in room dining", "inroom dining"]),
            ("housekeeping", ["housekeeping", "cleanliness", "cleaning", "spotless"]),
            ("hotel staff", ["staff", "hospitality", "concierge", "reception"]),
            ("parking", ["parking", "car park", "parking lot"]),
            ("airport transfer", ["airport", "airport transfer", "airport shuttle"]),
            ("transportation", ["transportation", "transport", "taxi", "shuttle"]),
            ("museum", ["museum", "archaeological museum"]),
            ("temple", ["temple", "temples"]),
            ("landmark attractions", ["attraction", "attractions", "sightseeing", "landmark"]),
            ("swimming pool", ["pool", "swimming"]),
            ("gym fitness", ["gym", "fitness center", "fitness centre"]),
            ("spa wellness", ["spa", "wellness", "massage", "sauna"]),
            ("family vacation", ["family", "families", "kids", "children"]),
            ("business center", ["business center", "business centre", "meeting", "conference"]),
            ("check in reception", ["check in", "checkin", "arrival", "reception"]),
            ("check out departure", ["check out", "checkout", "departure"]),
            ("hotel price", ["price", "cost", "per night", "budget", "affordable"]),
            ("hotel reviews", ["review", "reviews", "rating", "ratings", "score"]),
            ("hotel balcony", ["balcony", "terrace", "patio", "veranda"]),
            ("beach", ["beach", "beachfront", "ocean", "sea", "coast", "shore"]),
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
        ]

        negative = {
            "parking": [
                "no parking", "no parking space", "no parking spaces",
                "parking unavailable", "does not offer parking",
                "doesnt offer parking", "without parking"
            ]
        }

        found = []
        for label, words in concepts:
            if any(w in t for w in words):
                if label == "parking" and any(x in t for x in negative["parking"]):
                    continue
                found.append(label)

        # Hotel-specific phrases beat generic travel terms.
        if found:
            return " ".join(found[:3])

        # Use the existing scene classifier only when the sentence has no
        # explicit concept.
        scene_defaults = {
            "room": "hotel room interior",
            "rooms": "hotel room interior",
            "amenity": "hotel amenities",
            "dining": "hotel restaurant dining",
            "location": "hotel location city center",
            "review": "hotel review",
            "intro": "hotel exterior",
            "outside": "hotel exterior",
        }
        scene_text = str(scene).lower()
        for key, value in scene_defaults.items():
            if key in scene_text:
                return value

        return None

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

    def select_visual(
        self,
        text,
        is_first=False,
    ):

        scene_data = self.scene.analyze(text)
        scene = scene_data["scene"]

        prompt = self.build_visual_query(
            text=text,
            scene=scene,
        )

        if not prompt:
            prompt = self.keyword_query_for_sentence(text)

        if not prompt:
            prompt = self.query_generator.generate(
                text=text,
                scene=scene,
            )

        print(f"[SEARCH QUERY] {prompt}")
        self.visual_count += 1

        # First visual: explicit intro gets priority; otherwise first segment.
        if is_first:
            result = self.find_first_original(
                text=text,
                scene=scene,
            )
            if result:
                return result

        # Relevant stock image target. Never use a generic topic here.
        if self.should_try_stock_image():
            print("[MIX] Trying relevant stock image...")
            result = self.find_stock_image(query=prompt)
            if result:
                return result

        # Prefer an unused original hotel image.
        result = self.find_original(
            text=prompt,
            scene=scene,
        )
        if result:
            return result

        # Original unavailable -> stock video.
        result = self.find_stock_video(query=prompt)
        if result:
            self.stock_video_count += 1
            return result

        # Final attempt: relevant stock image.
        result = self.find_stock_image(query=prompt)
        if result:
            return result

        # IMPORTANT: never return None for a timeline segment. A missing
        # visual causes the renderer to hold the previous visual for the
        # entire segment. Use a controlled hotel/travel fallback instead.
        fallback_queries = [
            "hotel interior travel",
            "hotel exterior resort",
            "hotel lobby",
            "hotel room",
        ]

        for fallback in fallback_queries:
            result = self.find_stock_video(query=fallback)
            if result:
                self.stock_video_count += 1
                print(f"[FALLBACK VISUAL] {fallback}")
                return result

        for fallback in fallback_queries:
            result = self.find_stock_image(query=fallback)
            if result:
                print(f"[FALLBACK IMAGE] {fallback}")
                return result

        print("[WARNING] No visual source available for this sentence.")
        return None

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

        # Locate an explicit "intro" segment and render it first.
        # All other segment order/selection logic remains unchanged.
        intro_index = None

        for idx, segment in enumerate(segments):
            segment_text = str(
                segment.get("text", "")
            ).strip().lower()

            if segment_text == "intro" or segment_text.startswith("intro:") or segment_text.startswith("[intro]"):
                intro_index = idx
                break

        ordered_segments = list(enumerate(segments))

        if intro_index is not None and intro_index != 0:
            intro_item = ordered_segments.pop(intro_index)
            ordered_segments.insert(0, intro_item)

        for position, (i, segment) in enumerate(
            ordered_segments
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

            visual = (
                self.select_visual(
                    text,
                    is_first=(position == 0),
                )
            )

            if visual is None:

                continue

            timeline.append({

                "start": start,

                "end": end,

                "duration": duration,

                "text": text,

                "media": visual[
                    "media"
                ],

                "media_type": visual[
                    "media_type"
                ],

                "source_type": visual[
                    "source_type"
                ],

                "label": visual[
                    "label"
                ],

                "score": visual[
                    "score"
                ],

            })

            print(
                f"SOURCE: "
                f"{visual['source_type']}"
            )

            print(
                f"MEDIA: "
                f"{Path(visual['media']).name}"
            )

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