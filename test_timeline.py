from pathlib import Path

from config import (
    VOICE_FILE,
    ORIGINAL_IMAGES_DIR,
)

from src.timeline_builder import TimelineBuilder


def main():

    print("=" * 60)
    print("HOTEL REVIEW TIMELINE TEST")
    print("=" * 60)

    print()
    print("Voice :", VOICE_FILE)
    print("Images:", ORIGINAL_IMAGES_DIR)
    print()

    if not VOICE_FILE.exists():
        raise RuntimeError(
            f"Voice file missing: {VOICE_FILE}"
        )

    if not ORIGINAL_IMAGES_DIR.exists():
        raise RuntimeError(
            f"Images folder missing: "
            f"{ORIGINAL_IMAGES_DIR}"
        )

    builder = TimelineBuilder(
        audio_file=VOICE_FILE,
        images_dir=ORIGINAL_IMAGES_DIR,
    )

    timeline = builder.build()

    print()
    print("=" * 60)
    print("FINAL TIMELINE")
    print("=" * 60)

    for i, item in enumerate(
        timeline,
        start=1
    ):

        print(
            f"{i:03d} | "
            f"{item['start']:.2f} -> "
            f"{item['end']:.2f} | "
            f"{item['media_type']:5} | "
            f"{item['source_type']:12} | "
            f"{Path(item['media']).name}"
        )

    print()
    print(
        f"Total timeline items: "
        f"{len(timeline)}"
    )


if __name__ == "__main__":
    main()