from faster_whisper import WhisperModel

from config import WHISPER_MODEL, LANGUAGE


MIN_SEGMENT = 1.8
MAX_SEGMENT = 3.2


class TranscriptGenerator:

    def __init__(self):

        print(
            f"[INFO] Loading Whisper model: {WHISPER_MODEL}"
        )

        # Prefer CUDA when available; automatically fall back to CPU.
        try:
            import ctranslate2
            cuda_ok = ctranslate2.get_cuda_device_count() > 0
        except Exception:
            cuda_ok = False

        if cuda_ok:
            device = "cuda"
            compute_type = "float16"
            print("[INFO] Whisper device : CUDA")
        else:
            device = "cpu"
            compute_type = "int8"
            print("[INFO] Whisper device : CPU")

        self.model = WhisperModel(
            WHISPER_MODEL,
            device=device,
            compute_type=compute_type,
        )

    # -----------------------------------------------------

    def _make_chunk(
        self,
        words,
        start,
        end,
    ):

        return {
            "start": float(start),
            "end": float(end),
            "duration": float(end - start),
            "text": " ".join(
                w.word.strip()
                for w in words
            ).strip(),
        }

    # -----------------------------------------------------

    def _split_segment(
        self,
        segment,
    ):

        words = segment.words or []

        duration = float(
            segment.end - segment.start
        )

        if (
            not words
            or duration <= MAX_SEGMENT
        ):
            return [
                {
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "duration": duration,
                    "text": segment.text.strip(),
                }
            ]

        chunks = []

        current = []
        current_start = float(words[0].start)

        for word in words:

            current.append(word)

            elapsed = float(
                word.end - current_start
            )

            split = False

            if word.word.strip().endswith(
                (".", "!", "?")
            ):
                split = True

            elif elapsed >= 3.0:
                split = True

            if split:

                chunks.append(
                    self._make_chunk(
                        current,
                        current_start,
                        float(word.end),
                    )
                )

                current = []

                if word != words[-1]:
                    current_start = float(word.end)

        if current:

            chunks.append(
                self._make_chunk(
                    current,
                    current_start,
                    float(words[-1].end),
                )
            )

        # -------------------------------------------------
        # Merge very short chunks
        # -------------------------------------------------

        merged = []

        for chunk in chunks:

            if (
                merged
                and chunk["duration"] < MIN_SEGMENT
            ):

                merged[-1]["end"] = chunk["end"]

                merged[-1]["duration"] = (
                    merged[-1]["end"]
                    - merged[-1]["start"]
                )

                merged[-1]["text"] += (
                    " " + chunk["text"]
                )

            else:

                merged.append(chunk)

        return merged

    # -----------------------------------------------------

    def transcribe(self, audio_file):
        """
        Transcribe and group Whisper words into real spoken sentences.
        We do NOT force a 1.8-3.2 second split. A sentence stays intact until
        '.', '!' or '?' is reached. Every non-empty word is preserved.
        """
        segments, info = self.model.transcribe(
            str(audio_file),
            language=LANGUAGE,
            vad_filter=False,
            beam_size=5,
            word_timestamps=True,
            condition_on_previous_text=True,
        )

        results = []

        current_words = []
        current_start = None

        def flush():
            nonlocal current_words, current_start
            if not current_words:
                return
            text = " ".join(
                w.word.strip() for w in current_words if w.word.strip()
            ).strip()
            if text:
                results.append({
                    "start": float(current_start),
                    "end": float(current_words[-1].end),
                    "duration": float(current_words[-1].end - current_start),
                    "text": text,
                })
            current_words = []
            current_start = None

        for segment in segments:
            words = segment.words or []
            if not words:
                text = str(segment.text).strip()
                if not text:
                    continue
                if current_words:
                    flush()
                results.append({
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "duration": float(segment.end - segment.start),
                    "text": text,
                })
                continue

            for word in words:
                token = word.word.strip()
                if not token:
                    continue

                if current_start is None:
                    current_start = float(word.start)

                current_words.append(word)

                # Full-stop/question/exclamation are the real sentence boundary.
                if token.endswith((".", "!", "?")):
                    flush()

        flush()

        print(f"[INFO] Language : {info.language}")
        print(f"[INFO] Sentences : {len(results)}")
        if results:
            print(f"[INFO] Transcript End : {results[-1]['end']:.2f} sec")

        return results
