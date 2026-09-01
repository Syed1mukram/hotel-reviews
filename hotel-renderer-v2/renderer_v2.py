import os
import subprocess
import json
from pathlib import Path

BASE = Path("/kaggle/input/datasets/syed93/hotel-video-input/input")
IMG_DIR = BASE / "images"
STOCK_DIR = BASE / "stock"
VOICE = BASE / "voice.mp3"
OUT = Path("/kaggle/working/final_hotel_video_v2.mp4")

FPS = 30
W, H = 1920, 1080

def run(cmd):
    print("RUN:", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)

def duration(path):
    r = subprocess.run([
        "ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)
    ], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())

# Images
images = sorted(IMG_DIR.glob("*.jpg")) + sorted(IMG_DIR.glob("*.jpeg")) + sorted(IMG_DIR.glob("*.png"))
images = sorted(set(images), key=lambda p: p.name.lower())

# Optional local stock clips. Put .mp4/.mov/.webm files in input/stock/
stock = []
if STOCK_DIR.exists():
    stock = sorted(
        list(STOCK_DIR.glob("*.mp4")) +
        list(STOCK_DIR.glob("*.mov")) +
        list(STOCK_DIR.glob("*.webm")),
        key=lambda p: p.name.lower()
    )

print("Hotel images:", len(images))
print("Stock clips:", len(stock))
print("Voice:", VOICE.exists())

voice_dur = duration(VOICE)
print(f"Voice duration: {voice_dur:.2f} sec")

# Build a visually varied sequence:
# mostly hotel images, with stock clips inserted between image groups.
# Stock clips are optional; without them the renderer still works.
sequence = []
if stock:
    # Use stock clips at roughly 15%, 35%, 55%, 75%, 90% of the image sequence.
    stock_positions = set(round(x * max(1, len(images)-1)) for x in [0.15,0.35,0.55,0.75,0.90])
    si = 0
    for i, img in enumerate(images):
        sequence.append(("image", img))
        if i in stock_positions and si < len(stock):
            sequence.append(("stock", stock[si]))
            si += 1
else:
    sequence = [("image", x) for x in images]

# Each visual gets an equal share. Crossfade is applied between visuals.
visual_count = len(sequence)
per = voice_dur / visual_count
transition = min(0.55, per * 0.12)

# Create each visual as a short 1080p clip with subtle motion.
clips = Path("/kaggle/working/render_clips")
if clips.exists():
    shutil.rmtree(clips)
clips.mkdir()

clip_paths = []

for idx, (kind, path) in enumerate(sequence):
    out = clips / f"{idx:03d}.mp4"
    if kind == "image":
        # Slow zoom + gentle horizontal movement. No cropping of the source image.
        frames = max(2, int(per * FPS))
        vf = (
            f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
            f"crop={W*2}:{H*2},"
            f"zoompan=z='min(zoom+0.0008,1.10)':"
            f"x='iw/2-(iw/zoom/2)+sin(on/70)*18':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d=1:s={W}x{H}:fps={FPS},"
            "format=yuv420p"
        )
        run([
            "ffmpeg","-y","-loop","1","-i",str(path),
            "-t",f"{per:.3f}","-vf",vf,
            "-c:v","libx264","-preset","fast","-crf","20",
            "-pix_fmt","yuv420p","-an",str(out)
        ])
    else:
        # Stock clip: center-crop/scale to 16:9 and loop/trim to allotted time.
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},format=yuv420p"
        )
        run([
            "ffmpeg","-y","-stream_loop","-1","-i",str(path),
            "-t",f"{per:.3f}","-vf",vf,
            "-r",str(FPS),"-c:v","libx264","-preset","fast","-crf","20",
            "-pix_fmt","yuv420p","-an",str(out)
        ])
    clip_paths.append(out)

# Concatenate clips with simple clean cuts first.
# This is intentionally stable; the next pass can add crossfades after visual review.
concat = Path("/kaggle/working/clips.txt")
with concat.open("w") as f:
    for p in clip_paths:
        f.write(f"file '{p}'\n")

slideshow = Path("/kaggle/working/slideshow_v2.mp4")
run([
    "ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),
    "-c","copy","-movflags","+faststart",str(slideshow)
])

# Attach the exact narration length.
run([
    "ffmpeg","-y","-i",str(slideshow),"-i",str(VOICE),
    "-map","0:v:0","-map","1:a:0",
    "-c:v","copy","-c:a","aac","-b:a","192k",
    "-t",f"{voice_dur:.3f}",
    "-movflags","+faststart",str(OUT)
])

print("\nDONE ✅")
print("Output:", OUT)
print(f"Duration: {duration(OUT):.2f} sec")
print("Stock clips used:", len(stock))
