from pathlib import Path
from collections import deque

import torch
import open_clip
from PIL import Image

from src.utils import get_images


class ImageMatcher:

    def __init__(self):

        print("[INFO] Loading CLIP model...")

        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        self.model, _, self.preprocess = (
            open_clip.create_model_and_transforms(
                "ViT-B-32",
                pretrained="laion2b_s34b_b79k",
            )
        )

        self.model = (
            self.model
            .to(self.device)
            .eval()
        )

        self.tokenizer = open_clip.get_tokenizer(
            "ViT-B-32"
        )

        self.image_data = []

        self.used_images = set()
        self.recent_images = deque(maxlen=3)

    # -----------------------------------------------------

    @torch.no_grad()
    def index_images(self, image_folder: Path):

        self.image_data.clear()
        self.used_images.clear()
        self.recent_images.clear()

        images = get_images(image_folder)

        print(
            f"[INFO] Indexing {len(images)} "
            f"original hotel images..."
        )

        for image_path in images:

            try:

                image = (
                    Image.open(image_path)
                    .convert("RGB")
                )

                tensor = (
                    self.preprocess(image)
                    .unsqueeze(0)
                    .to(self.device)
                )

                feature = self.model.encode_image(
                    tensor
                )

                feature = (
                    feature
                    / feature.norm(
                        dim=-1,
                        keepdim=True
                    )
                )

                self.image_data.append({
                    "path": image_path,
                    "feature": feature.cpu(),
                })

            except Exception as e:

                print(
                    f"[WARNING] Skipped "
                    f"{image_path.name}: {e}"
                )

        print(
            f"[INFO] Indexed "
            f"{len(self.image_data)} images."
        )

    # -----------------------------------------------------

    @torch.no_grad()
    def _encode_text(self, text):

        tokens = self.tokenizer(
            [text]
        ).to(self.device)

        feature = self.model.encode_text(
            tokens
        )

        feature = (
            feature
            / feature.norm(
                dim=-1,
                keepdim=True
            )
        )

        return feature.cpu()

    # -----------------------------------------------------
    # Category-specific prompts
    # -----------------------------------------------------

    def _category_prompts(self, scene):

        prompts = {

            "room": [
                "hotel room",
                "hotel bedroom",
                "hotel suite",
                "bedroom with bed",
            ],

            "bathroom": [
                "hotel bathroom",
                "luxury bathroom",
                "hotel shower",
                "hotel bathtub",
            ],

            "pool": [
                "hotel swimming pool",
                "resort pool",
                "infinity pool",
                "hotel pool",
            ],

            "beach": [
                "hotel beach",
                "resort beach",
                "tropical beach",
                "ocean beach",
            ],

            "restaurant": [
                "hotel restaurant",
                "hotel dining",
                "hotel breakfast",
                "resort restaurant",
            ],

            "bar": [
                "hotel bar",
                "resort bar",
                "cocktail bar",
                "hotel lounge",
            ],

            "spa": [
                "hotel spa",
                "resort spa",
                "massage spa",
                "wellness center",
            ],

            "gym": [
                "hotel gym",
                "hotel fitness center",
                "resort gym",
            ],

            "lobby": [
                "hotel lobby",
                "hotel reception",
                "hotel entrance",
                "hotel front desk",
            ],

            "balcony": [
                "hotel balcony",
                "hotel terrace",
                "hotel ocean view",
                "hotel room view",
            ],

            "kids": [
                "hotel kids club",
                "family resort",
                "children hotel activities",
                "hotel playground",
            ],

            "outside": [
                "hotel exterior",
                "resort exterior",
                "hotel building",
                "hotel property",
            ],

            "general": [
                "hotel",
                "resort",
                "hotel property",
                "hotel travel",
            ],
        }

        return prompts.get(
            scene,
            prompts["general"]
        )

    # -----------------------------------------------------

    @torch.no_grad()
    def find_best(
        self,
        prompt,
        scene="general",
    ):

        if not self.image_data:
            return None

        # Main narration meaning
        text_feature = self._encode_text(
            prompt
        )

        # Category meaning
        category_prompts = (
            self._category_prompts(scene)
        )

        category_features = []

        for category_prompt in category_prompts:

            feature = self._encode_text(
                category_prompt
            )

            category_features.append(
                feature
            )

        candidates = []

        for item in self.image_data:

            image_path = item["path"]

            # STRICT ONE-TIME USE
            if image_path in self.used_images:
                continue

            if image_path in self.recent_images:
                continue

            image_feature = item[
                "feature"
            ]

            # Narration score
            text_score = float(
                (
                    text_feature
                    @ image_feature.T
                ).item()
            )

            # Category score
            category_scores = []

            for feature in category_features:

                score = float(
                    (
                        feature
                        @ image_feature.T
                    ).item()
                )

                category_scores.append(
                    score
                )

            category_score = max(
                category_scores
            )

            # Combined score
            combined_score = (
                (text_score * 0.45)
                +
                (category_score * 0.55)
            )

            candidates.append({
                "path": image_path,
                "text_score": text_score,
                "category_score": category_score,
                "score": combined_score,
            })

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        best = candidates[0]

        # Don't accept extremely weak matches.
        if best["score"] < 0.14:
            return None

        image_path = best["path"]

        self.used_images.add(
            image_path
        )

        self.recent_images.append(
            image_path
        )

        print(
            f"[IMAGE MATCH] "
            f"{image_path.name} | "
            f"text={best['text_score']:.3f} | "
            f"category={best['category_score']:.3f} | "
            f"final={best['score']:.3f}"
        )

        return (
            image_path,
            best["score"]
        )

    # -----------------------------------------------------

    def mark_used(self, image_path):

        image_path = Path(
            image_path
        )

        self.used_images.add(
            image_path
        )

        self.recent_images.append(
            image_path
        )

    # -----------------------------------------------------

    def is_used(self, image_path):

        return Path(
            image_path
        ) in self.used_images

    # -----------------------------------------------------

    def remaining_images(self):

        return [
            item["path"]
            for item in self.image_data
            if item["path"]
            not in self.used_images
        ]

    # -----------------------------------------------------

    def reset(self):

        self.used_images.clear()
        self.recent_images.clear()