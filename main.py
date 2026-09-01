from config import VOICE_FILE, OUTPUT_VIDEO, ORIGINAL_IMAGES_DIR
from src.timeline_builder import TimelineBuilder
from src.renderer import Renderer


def main():
    print("========================================")
    print("HOTEL REVIEW PIPELINE")
    print("========================================")

    builder = TimelineBuilder(
        audio_file=VOICE_FILE,
        images_dir=ORIGINAL_IMAGES_DIR,
    )

    timeline = builder.build()

    renderer = Renderer()

    renderer.render(
        timeline=timeline,
        audio_file=VOICE_FILE,
        output=OUTPUT_VIDEO,
    )

    print("========================================")
    print("DONE")
    print("========================================")
    print(f"Final video: {OUTPUT_VIDEO}")


if __name__ == "__main__":
    main()
