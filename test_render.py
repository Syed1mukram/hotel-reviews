from config import (
    VOICE_FILE,
    ORIGINAL_IMAGES_DIR,
    OUTPUT_VIDEO,
)

from src.timeline_builder import TimelineBuilder
from src.renderer import Renderer


def main():

    builder = TimelineBuilder(
        audio_file=VOICE_FILE,
        images_dir=ORIGINAL_IMAGES_DIR,
    )

    timeline = builder.build()

    if not timeline:
        raise RuntimeError(
            "Timeline is empty."
        )

    renderer = Renderer()

    output = renderer.render(
        timeline=timeline,
        output=OUTPUT_VIDEO,
    )

    print()
    print(
        "FINAL VIDEO:"
    )
    print(
        output
    )


if __name__ == "__main__":
    main()