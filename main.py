from config import VOICE_FILE, ORIGINAL_IMAGES_DIR
from src.timeline_builder import TimelineBuilder
from editor_project import save_editor_project
from openshot_project_builder import build_openshot_project


def main():
    print("========================================")
    print("HOTEL REVIEW - LIGHTWEIGHT OPENSHOT")
    print("========================================")

    builder = TimelineBuilder(
        audio_file=VOICE_FILE,
        images_dir=ORIGINAL_IMAGES_DIR,
    )

    timeline = builder.build()
    print(f"Timeline items: {len(timeline)}")

    save_editor_project(
        timeline=timeline,
        audio_file=VOICE_FILE,
        output="editor_project.json",
    )

    build_openshot_project(
        editor_project="editor_project.json",
        template="openshot_template_clean.osp",
        output_dir="openshot_export",
        project_name="hotel_review",
    )


if __name__ == "__main__":
    main()
