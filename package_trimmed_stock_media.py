import json
import shutil
import subprocess
import zipfile
from pathlib import Path


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def resolve_media(root, raw):
    p = Path(str(raw))

    if p.exists():
        return p.resolve()

    raw_s = str(raw).replace("\\", "/")
    if "/hotel-reviews/" in raw_s:
        candidate = root / raw_s.split("/hotel-reviews/", 1)[1]
        if candidate.exists():
            return candidate.resolve()

    candidates = [
        root / "input" / "images" / p.name,
        root / "cache" / "stock" / p.name,
        root / "cache" / "stock_images" / p.name,
        root / "input" / p.name,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    matches = list(root.rglob(p.name))
    return matches[0].resolve() if matches else None


def trim_video(source, output, duration):
    output.parent.mkdir(parents=True, exist_ok=True)

    # The current timeline renderer uses the beginning of a stock video and
    # loops it when necessary, so package exactly the amount the timeline uses.
    cmd = [
        "ffmpeg", "-y",
        "-i", str(source),
        "-t", f"{max(0.05, duration):.3f}",
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed for {source.name}:\n{result.stderr[-2000:]}"
        )


def build_package(
    editor_project="editor_project.json",
    output_dir="openshot_media_package",
    zip_name="hotel_review_media_package.zip",
):
    root = Path(editor_project).resolve().parent
    project_path = root / editor_project
    out_dir = root / output_dir

    if not project_path.exists():
        raise FileNotFoundError(project_path)

    with open(project_path, "r", encoding="utf-8") as f:
        project = json.load(f)

    if out_dir.exists():
        shutil.rmtree(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)

    # Always include voice.
    audio = resolve_media(root, project.get("audio", "input/voice.mp3"))
    if audio is None:
        raise FileNotFoundError("Voice file not found.")

    audio_dest = out_dir / "input" / "voice.mp3"
    audio_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(audio, audio_dest)

    seen = set()
    packaged = []

    timeline = project.get("timeline", [])

    for index, item in enumerate(timeline):
        source_type = str(item.get("source_type", ""))
        media_type = str(item.get("media_type", ""))
        duration = float(item.get("duration", 0.0))
        media = resolve_media(root, item.get("media", ""))

        if media is None:
            print(f"[SKIP] Missing media: {item.get('media')}")
            continue

        # Original hotel images are already small and should remain full quality.
        if media_type == "image" or media.suffix.lower() in IMAGE_EXTS:
            key = ("image", media.resolve())
            if key in seen:
                continue
            seen.add(key)

            dest = out_dir / "input" / "images" / media.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(media, dest)
            packaged.append(dest)
            print(f"[IMAGE] {media.name}")

        # Stock videos are individually trimmed to exactly the timeline duration.
        elif source_type == "stock_video" or media_type == "video":
            key = ("video", media.resolve(), round(duration, 3), index)
            # Same source can legitimately appear in multiple places with
            # different required durations, so index stays in the cache key.
            if key in seen:
                continue
            seen.add(key)

            dest = (
                out_dir
                / "cache"
                / "stock"
                / f"{media.stem}_clip_{index:03d}.mp4"
            )

            trim_video(media, dest, duration)
            packaged.append(dest)
            print(
                f"[VIDEO] {media.name} -> "
                f"{dest.name} | {duration:.3f}s"
            )

    # Create a compact copy of editor_project.json using package-relative paths.
    compact = {
        "audio": "input/voice.mp3",
        "timeline": [],
    }

    # Map each timeline item to its packaged file.
    video_counter = 0
    image_map = {}
    video_map = {}

    for index, item in enumerate(timeline):
        media_type = str(item.get("media_type", ""))
        source_type = str(item.get("source_type", ""))
        media = resolve_media(root, item.get("media", ""))
        if media is None:
            continue

        if media_type == "image" or media.suffix.lower() in IMAGE_EXTS:
            key = str(media.resolve())
            if key not in image_map:
                image_map[key] = f"input/images/{media.name}"
            rel = image_map[key]
        else:
            rel = (
                f"cache/stock/"
                f"{media.stem}_clip_{index:03d}.mp4"
            )
            video_counter += 1

        compact["timeline"].append({
            "start": float(item["start"]),
            "end": float(item["end"]),
            "duration": float(item["duration"]),
            "text": item.get("text", ""),
            "media": rel,
            "media_type": "image" if media_type == "image" else "video",
            "source_type": source_type,
            "label": item.get("label"),
            "score": item.get("score"),
            "sentence_index": item.get("sentence_index"),
            "visual_piece": item.get("visual_piece"),
            "visual_pieces_total": item.get("visual_pieces_total"),
        })

    with open(
        out_dir / "editor_project.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            compact,
            f,
            ensure_ascii=False,
            indent=2,
        )

    zip_path = root / zip_name
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(
        zip_path,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as z:
        for path in out_dir.rglob("*"):
            if path.is_file():
                z.write(
                    path,
                    path.relative_to(out_dir).as_posix(),
                )

    size_mb = zip_path.stat().st_size / (1024 * 1024)

    print("========================================")
    print("MEDIA PACKAGE READY")
    print("========================================")
    print(f"Timeline items : {len(compact['timeline'])}")
    print(f"Package        : {zip_path}")
    print(f"Package size   : {size_mb:.1f} MB")
    print("Stock videos   : trimmed to timeline duration")
    print("Original images: full quality")
    print("========================================")

    return zip_path


if __name__ == "__main__":
    build_package()
