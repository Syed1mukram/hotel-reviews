from pathlib import Path
import subprocess
import cv2

from PIL import Image, ImageDraw, ImageFont

from config import (
    VOICE_FILE,
    OUTPUT_VIDEO,
    TEMP_DIR,
)

from .camera import Camera


class Renderer:

    WIDTH = 1920
    HEIGHT = 1080
    FPS = 30

    def __init__(self):

        self.temp_dir = Path(TEMP_DIR)
        self.temp_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.camera = Camera()

    # =========================================================
    # FFMPEG
    # =========================================================

    def run(self, cmd):

        print("\n[FFMPEG]")
        print(" ".join(str(x) for x in cmd))

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:

            print(result.stderr)

            raise RuntimeError(
                "FFmpeg failed."
            )

        return result

    # =========================================================
    # DURATION
    # =========================================================

    def get_duration(
        self,
        file_path
    ):

        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            return 0.0

        try:
            return float(
                result.stdout.strip()
            )
        except Exception:
            return 0.0

    # =========================================================
    # CHECK IMAGE
    # =========================================================

    def check_image(
        self,
        image_path
    ):

        image_path = Path(
            image_path
        )

        if not image_path.exists():

            raise RuntimeError(
                f"Image not found: "
                f"{image_path}"
            )

        try:

            with Image.open(
                image_path
            ) as img:

                img.verify()

        except Exception as e:

            raise RuntimeError(
                f"Invalid image: "
                f"{image_path}\n{e}"
            )

    # =========================================================
    # STOCK LABEL
    # =========================================================

    def create_label(
        self,
        text,
        filename
    ):

        image = Image.new(
            "RGBA",
            (500, 100),
            (0, 0, 0, 0)
        )

        draw = ImageDraw.Draw(
            image
        )

        try:

            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
                "arialbd.ttf",
            ]

            font = None

            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(
                        font_path,
                        42
                    )
                    break
                except Exception:
                    pass

            if font is None:
                raise RuntimeError(
                    "No suitable bold font found."
                )

        except Exception as e:

            raise RuntimeError(
                f"Could not load stock label font: {e}"
            )

        bbox = draw.textbbox(
            (0, 0),
            text,
            font=font
        )

        text_width = (
            bbox[2] - bbox[0]
        )

        text_height = (
            bbox[3] - bbox[1]
        )

        padding_x = 24
        padding_y = 18

        box_width = (
            text_width
            + padding_x * 2
        )

        box_height = (
            text_height
            + padding_y * 2
        )

        draw.rectangle(
            (
                0,
                0,
                box_width,
                box_height
            ),
            fill=(0, 0, 0, 225)
        )

        draw.text(
            (
                padding_x,
                padding_y - 5
            ),
            text,
            fill=(255, 255, 0, 255),
            font=font
        )

        output = (
            self.temp_dir
            / filename
        )

        image.save(
            output,
            "PNG"
        )

        return output

    # =========================================================
    # IMAGE
    # STABLE CAMERA ZOOM / PAN
    # =========================================================

    def render_image(
        self,
        image_path,
        duration,
        output,
        index=0
    ):

        self.check_image(
            image_path
        )

        frames = max(
            1,
            int(
                float(duration)
                * self.FPS
            )
        )

        print(
            f"[IMAGE] "
            f"{Path(image_path).name} "
            f"| {duration:.2f}s"
        )

        # -----------------------------------------------------
        # Load image
        # -----------------------------------------------------

        image = cv2.imread(
            str(image_path)
        )

        if image is None:

            raise RuntimeError(
                f"Could not load image: "
                f"{image_path}"
            )

        # -----------------------------------------------------
        # Resize image so camera has enough room
        # -----------------------------------------------------

        img_h, img_w = (
            image.shape[:2]
        )

        target_ratio = (
            self.WIDTH
            / self.HEIGHT
        )

        source_ratio = (
            img_w
            / img_h
        )

        if source_ratio > target_ratio:

            new_h = 1238

            new_w = int(
                new_h
                * source_ratio
            )

        else:

            new_w = 2200

            new_h = int(
                new_w
                / source_ratio
            )

        image = cv2.resize(
            image,
            (new_w, new_h),
            interpolation=cv2.INTER_LANCZOS4
        )

        # -----------------------------------------------------
        # Add padding like resort renderer
        # -----------------------------------------------------

        pad = 300

        image = cv2.copyMakeBorder(
            image,
            pad,
            pad,
            pad,
            pad,
            borderType=cv2.BORDER_REPLICATE
        )

        # -----------------------------------------------------
        # Select stable movement
        # -----------------------------------------------------

        motion = (
            self.camera.random_motion()
        )

        print(
            f"[CAMERA] "
            f"{motion}"
        )

        # -----------------------------------------------------
        # Temporary frame directory
        # -----------------------------------------------------

        frame_dir = (
            self.temp_dir
            / f"frames_{index:04d}"
        )

        frame_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # -----------------------------------------------------
        # Generate frames
        # -----------------------------------------------------

        for frame_number in range(
            frames
        ):

            if frames <= 1:

                progress = 1.0

            else:

                progress = (
                    frame_number
                    / (frames - 1)
                )

            frame = (
                self.camera.render(
                    image=image,
                    progress=progress,
                    motion=motion,
                    out_width=self.WIDTH,
                    out_height=self.HEIGHT
                )
            )

            frame_path = (
                frame_dir
                / f"{frame_number:06d}.jpg"
            )

            cv2.imwrite(
                str(frame_path),
                frame,
                [
                    int(
                        cv2.IMWRITE_JPEG_QUALITY
                    ),
                    95
                ]
            )

        # -----------------------------------------------------
        # Encode frames
        # -----------------------------------------------------

        pattern = (
            frame_dir
            / "%06d.jpg"
        )

        cmd = [

            "ffmpeg",
            "-y",

            "-framerate",
            str(self.FPS),

            "-i",
            str(pattern),

            "-t",
            str(duration),

            "-c:v",
            "h264_nvenc",

            "-preset",
            "medium",

            "-cq",
            "18",

            "-pix_fmt",
            "yuv420p",

            "-r",
            str(self.FPS),

            "-an",

            str(output)
        ]

        self.run(cmd)

        # -----------------------------------------------------
        # Cleanup frames
        # -----------------------------------------------------

        for frame in frame_dir.glob(
            "*.jpg"
        ):

            try:
                frame.unlink()
            except Exception:
                pass

        try:
            frame_dir.rmdir()
        except Exception:
            pass

    # =========================================================
    # STOCK VIDEO
    # =========================================================

    def render_video(
        self,
        video_path,
        duration,
        output
    ):

        video_path = Path(
            video_path
        )

        if not video_path.exists():

            raise RuntimeError(
                f"Video not found: "
                f"{video_path}"
            )

        filter_video = (
            "scale=2112:1188:"
            "force_original_aspect_ratio=increase,"
            "crop=1920:1080:"
            "(in_w-1920)/2:"
            "(in_h-1080)/2,"
            "setsar=1"
        )

        cmd = [

            "ffmpeg",
            "-y",

            "-stream_loop",
            "-1",

            "-i",
            str(video_path),

            "-t",
            str(duration),

            "-vf",
            filter_video,

            "-an",

            "-c:v",
            "h264_nvenc",

            "-preset",
            "medium",

            "-cq",
            "18",

            "-pix_fmt",
            "yuv420p",

            "-r",
            str(self.FPS),

            str(output)
        ]

        self.run(cmd)

    # =========================================================
    # ADD STOCK LABEL
    # =========================================================

    def add_label(
        self,
        video_path,
        label,
        duration,
        output
    ):

        label_file = (
            self.create_label(
                label,
                "stock_label.png"
            )
        )

        cmd = [

            "ffmpeg",
            "-y",

            "-i",
            str(video_path),

            "-i",
            str(label_file),

            "-filter_complex",

            (
                "[1:v]format=rgba[label];"
                "[0:v][label]"
                "overlay=W-w-35:35"
            ),

            "-t",
            str(duration),

            "-an",

            "-c:v",
            "h264_nvenc",

            "-preset",
            "medium",

            "-cq",
            "18",

            "-pix_fmt",
            "yuv420p",

            "-r",
            str(self.FPS),

            str(output)
        ]

        self.run(cmd)

    # =========================================================
    # RENDER ITEM
    # =========================================================

    def render_item(
        self,
        item,
        index
    ):

        media = Path(
            item["media"]
        )

        duration = float(
            item["duration"]
        )

        source_type = (
            item["source_type"]
        )

        base = (
            self.temp_dir
            / f"{index:04d}_base.mp4"
        )

        final = (
            self.temp_dir
            / f"{index:04d}.mp4"
        )

        print(
            f"\n[{index:04d}] "
            f"{source_type} | "
            f"{duration:.2f}s | "
            f"{media.name}"
        )

        # -----------------------------------------------------
        # ORIGINAL / STOCK IMAGE
        # -----------------------------------------------------

        if source_type in (
            "original",
            "stock_image"
        ):

            self.render_image(
                image_path=media,
                duration=duration,
                output=base,
                index=index
            )

        # -----------------------------------------------------
        # STOCK VIDEO
        # -----------------------------------------------------

        elif source_type == (
            "stock_video"
        ):

            self.render_video(
                video_path=media,
                duration=duration,
                output=base
            )

        else:

            raise RuntimeError(
                f"Unknown source type: "
                f"{source_type}"
            )

        # -----------------------------------------------------
        # LABEL
        # -----------------------------------------------------

        label = item.get(
            "label"
        )

        if label:

            self.add_label(
                video_path=base,
                label=label,
                duration=duration,
                output=final
            )

            return final

        return base

    # =========================================================
    # CONCATENATE
    # =========================================================

    def concatenate(
        self,
        clips,
        output
    ):

        concat_file = (
            self.temp_dir
            / "concat.txt"
        )

        with open(
            concat_file,
            "w",
            encoding="utf-8"
        ) as f:

            for clip in clips:

                path = (
                    Path(clip)
                    .resolve()
                    .as_posix()
                )

                f.write(
                    f"file '{path}'\n"
                )

        cmd = [

            "ffmpeg",
            "-y",

            "-f",
            "concat",

            "-safe",
            "0",

            "-i",
            str(concat_file),

            "-c:v",
            "h264_nvenc",

            "-preset",
            "medium",

            "-cq",
            "18",

            "-pix_fmt",
            "yuv420p",

            "-r",
            str(self.FPS),

            "-an",

            str(output)
        ]

        self.run(cmd)

    # =========================================================
    # ADD VOICE
    # =========================================================

    def add_voice(
        self,
        video_file,
        audio_file,
        output
    ):

        print(
            "\n[INFO] Adding voiceover..."
        )

        voice_duration = self.get_duration(audio_file)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_file),
            "-i",
            str(audio_file),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-t",
            str(voice_duration),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(output)
        ]

        self.run(cmd)

    # =========================================================
    # FULL RENDER
    # =========================================================

    def render(
        self,
        timeline,
        output=None
    ):

        if output is None:
            output = OUTPUT_VIDEO

        output = Path(
            output
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # -----------------------------------------------------
        # Clean temporary MP4 files
        # -----------------------------------------------------

        for file in (
            self.temp_dir.glob(
                "*.mp4"
            )
        ):

            try:
                file.unlink()
            except Exception:
                pass

        clips = []

        print(
            "\n========================================"
        )

        print(
            "RENDERING HOTEL REVIEW"
        )

        print(
            "========================================"
        )

        # -----------------------------------------------------
        # Render timeline
        # -----------------------------------------------------

        for index, item in enumerate(
            timeline
        ):

            clip = (
                self.render_item(
                    item,
                    index
                )
            )

            clips.append(
                clip
            )

        if not clips:

            raise RuntimeError(
                "No clips rendered."
            )

        # -----------------------------------------------------
        # Concatenate
        # -----------------------------------------------------

        silent_video = (
            self.temp_dir
            / "silent_video.mp4"
        )

        self.concatenate(
            clips,
            silent_video
        )

        # -----------------------------------------------------
        # Add voice
        # -----------------------------------------------------

        self.add_voice(
            video_file=silent_video,
            audio_file=VOICE_FILE,
            output=output
        )

        # -----------------------------------------------------
        # Final information
        # -----------------------------------------------------

        final_duration = (
            self.get_duration(
                output
            )
        )

        voice_duration = (
            self.get_duration(
                VOICE_FILE
            )
        )

        print(
            "\n========================================"
        )

        print(
            "[SUCCESS] HOTEL REVIEW CREATED"
        )

        print(
            f"Final video : "
            f"{final_duration:.3f}s"
        )

        print(
            f"Voice       : "
            f"{voice_duration:.3f}s"
        )

        print(
            f"Output      : "
            f"{output}"
        )

        print(
            "========================================"
        )

        return output