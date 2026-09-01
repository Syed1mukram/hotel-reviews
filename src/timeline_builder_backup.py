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
    # VISUAL SELECTION
    # =========================================================

    def select_visual(
        self,
        text,
        is_first=False,
    ):

        scene_data = self.scene.analyze(text)
        scene = scene_data["scene"]

        prompt = self.query_generator.generate(
            text=text,
            scene=scene,
        )

        print(f"[SEARCH QUERY] {prompt}")
        self.visual_count += 1

        # First visual must be an original hotel image.
        if is_first:
            result = self.find_first_original(
                text=text,
                scene=scene,
            )
            if result:
                return result

        # Approximately 15% relevant stock images.
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

        # If no relevant unused original exists, use stock video.
        result = self.find_stock_video(query=prompt)
        if result:
            self.stock_video_count += 1
            return result

        # Last relevant stock-image attempt.
        result = self.find_stock_image(query=prompt)
        if result:
            return result

        print("[WARNING] No relevant visual found:")
        print(text)
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

            if "intro" in segment_text:
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