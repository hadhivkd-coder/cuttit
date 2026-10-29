"""Speech-to-text with Gemini. Returns timed segments per clip."""

import json
from pathlib import Path

import httpx
from google import genai
from google.genai import errors, types

from .config import settings
from .media import duration, extract_audio, has_audio
from .models import ClipTranscript, Segment

PROMPT = """Transcribe this audio. The speaker may use Malayalam, English, or a mix (Manglish).
Write Malayalam in Malayalam script and English words in English, exactly as spoken.
Split into short phrases of at most about 8 words. Include filler words (umm, aah, like),
false starts and repeated takes, because the editor needs to see them to cut them out.
Times are seconds from the start of the audio, accurate to 0.1 s.
Return JSON: {"language": "ml" | "en" | "mixed", "segments": [{"start": float, "end": float, "text": str}]}
If nobody speaks, return {"language": "ml", "segments": []}."""

_SCHEMA = {
    "type": "object",
    "properties": {
        "language": {"type": "string", "enum": ["ml", "en", "mixed"]},
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "text": {"type": "string"},
                },
                "required": ["start", "end", "text"],
            },
        },
    },
    "required": ["language", "segments"],
}

_INLINE_LIMIT = 15 * 1024 * 1024


def _client() -> genai.Client:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    # Fail fast (2 min) on a stuck request so the fallback model or the job retry can take over.
    return genai.Client(api_key=settings.gemini_api_key, http_options=types.HttpOptions(timeout=120_000))


def transcribe_clip(index: int, clip: Path, work: Path) -> ClipTranscript:
    clip_len = duration(clip)
    if not has_audio(clip):
        return ClipTranscript(clip=index, duration=clip_len)

    audio = extract_audio(clip, work / f"audio_{index}.mp3")
    client = _client()
    if audio.stat().st_size <= _INLINE_LIMIT:
        media = types.Part.from_bytes(data=audio.read_bytes(), mime_type="audio/mp3")
    else:
        media = client.files.upload(file=str(audio))

    config = types.GenerateContentConfig(
        response_mime_type="application/json", response_schema=_SCHEMA, temperature=0)
    models = [settings.gemini_model, *settings.gemini_fallbacks]
    for i, model in enumerate(models):
        try:
            resp = client.models.generate_content(model=model, contents=[media, PROMPT], config=config)
            break
        except (errors.ServerError, errors.ClientError, httpx.HTTPError) as exc:
            # Overloaded, timed out or retired model: try the next one.
            if i == len(models) - 1 or getattr(exc, "code", 503) not in (404, 429, 500, 503, 504):
                raise
    data = json.loads(resp.text)
    segments = []
    for s in data.get("segments", []):
        start = max(0.0, float(s["start"]))
        end = min(clip_len, float(s["end"]))
        if end > start and s["text"].strip():
            segments.append(Segment(start=start, end=end, text=s["text"].strip()))
    return ClipTranscript(clip=index, duration=clip_len,
                          language=data.get("language", "ml"), segments=segments)


def transcribe_all(clips: list[Path], work: Path) -> list[ClipTranscript]:
    return [transcribe_clip(i, c, work) for i, c in enumerate(clips)]
