from config import VOICE_FILE, OUTPUT_VIDEO, ORIGINAL_IMAGES_DIR
from src.timeline_builder import TimelineBuilder
from src.renderer import Renderer


def run_review():
    from review_plan import build_review_plan
    build_review_plan()

    import kaggle_visual_review_exact
    kaggle_visual_review_exact.launch_review()


def run_render():
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
        output=OUTPUT_VIDEO,
    )

    print("========================================")
    print("DONE")
    print("========================================")
    print(f"Final video: {OUTPUT_VIDEO}")


def main():
    import sys

    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "render"

    if mode == "review":
        run_review()
        return

    if mode == "render":
        run_render()
        return

    raise SystemExit(
        "Usage: python main.py review\n"
        "       python main.py render"
    )


if __name__ == "__main__":
    main()
