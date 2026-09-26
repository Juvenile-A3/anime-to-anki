from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
from typing import Any
import unicodedata
from urllib.parse import unquote, urlsplit

from .anki import AnkiConnectResult, add_note_via_ankiconnect
from .ass import extract_bilingual_from_ass
from .config import AppConfig, resolved_output_root
from .text import normalize_japanese_text, split_bilingual


@dataclass(frozen=True)
class ClipWindow:
    start: float
    end: float

    @property
    def length(self) -> float:
        return self.end - self.start


@dataclass(frozen=True)
class CaptureResult:
    japanese: str
    chinese: str
    clip_path: Path
    tsv_path: Path
    manifest_path: Path
    clip_window: ClipWindow
    anki: AnkiConnectResult | None
    anki_error: str | None = None


def capture_from_payload(payload: dict[str, Any], config: AppConfig) -> CaptureResult:
    media_path = _resolve_media_path(payload)
    output_root = resolved_output_root(config)
    output_root.mkdir(parents=True, exist_ok=True)

    window = compute_clip_window(payload, config)
    japanese, chinese = _extract_subtitle_text(payload, config, media_path)
    japanese = normalize_japanese_text(japanese)
    clip_path = _next_clip_path(
        output_root,
        media_path,
        window,
        config.output.clip_extension,
        media_title=payload.get("media_title"),
    )

    _extract_clip(media_path, clip_path, window, config)

    japanese_html = _field_html(japanese)
    chinese_html = _field_html(chinese)
    source_html = _field_html(_source_text(payload, media_path, window))
    media_html = _media_field(clip_path.name, config.output.media_reference)

    tsv_path = output_root / config.output.tsv_name
    manifest_path = output_root / config.output.manifest_name

    anki_result = None
    anki_error = None
    if config.anki.enabled:
        try:
            anki_result = add_note_via_ankiconnect(
                config=config.anki,
                japanese_html=japanese_html,
                chinese_html=chinese_html,
                media_html=media_html,
                source_html=source_html,
                media_path=clip_path,
            )
        except Exception as exc:  # Keep local import files if Anki is closed.
            anki_error = str(exc)

    if _should_append_tsv(config, anki_error):
        _append_tsv(tsv_path, [japanese_html, chinese_html, media_html, source_html])

    if anki_result and not config.output.keep_media:
        _delete_file_if_exists(clip_path)

    _append_manifest(
        manifest_path,
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "media_path": str(media_path),
            "clip_path": str(clip_path),
            "clip_kept": clip_path.exists(),
            "start": window.start,
            "end": window.end,
            "japanese": japanese,
            "chinese": chinese,
            "payload": payload,
            "anki_note_id": anki_result.note_id if anki_result else None,
            "anki_error": anki_error,
        },
    )

    return CaptureResult(
        japanese=japanese,
        chinese=chinese,
        clip_path=clip_path,
        tsv_path=tsv_path,
        manifest_path=manifest_path,
        clip_window=window,
        anki=anki_result,
        anki_error=anki_error,
    )


def compute_clip_window(payload: dict[str, Any], config: AppConfig) -> ClipWindow:
    time_pos = _float_or_none(payload.get("time_pos")) or 0.0
    duration = _float_or_none(payload.get("duration"))
    sub_start = _float_or_none(payload.get("sub_start"))
    sub_end = _float_or_none(payload.get("sub_end"))

    if sub_start is not None and sub_end is not None and sub_end > sub_start:
        start = sub_start - config.output.padding_before
        end = sub_end + config.output.padding_after
    else:
        start = time_pos - config.output.fallback_before
        end = time_pos + config.output.fallback_after

    start = max(0.0, start)
    if duration is not None:
        end = min(duration, end)

    start, end = _enforce_length(
        start=start,
        end=end,
        center=time_pos,
        minimum=config.output.min_clip_seconds,
        maximum=config.output.max_clip_seconds,
        duration=duration,
    )
    return ClipWindow(start=round(start, 3), end=round(end, 3))


def load_payload_file(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_payload_json(raw: str) -> dict[str, Any]:
    return json.loads(raw)


def _extract_subtitle_text(
    payload: dict[str, Any],
    config: AppConfig,
    media_path: Path | str | None = None,
) -> tuple[str, str]:
    subtitle_path = _resolve_optional_path(
        payload.get("subtitle_path"),
        payload.get("working_directory"),
    )
    subtitle_paths: list[Path] = []
    if subtitle_path:
        subtitle_paths.append(subtitle_path)
    if isinstance(media_path, Path):
        subtitle_paths.extend(_sibling_subtitle_paths(media_path))

    for subtitle_path in _unique_existing_paths(subtitle_paths):
        if subtitle_path.suffix.lower() not in {".ass", ".ssa"}:
            continue
        ass_result = extract_bilingual_from_ass(
            subtitle_path,
            time_pos=_float_or_none(payload.get("time_pos")),
            sub_start=_float_or_none(payload.get("sub_start")),
            sub_end=_float_or_none(payload.get("sub_end")),
            config=config.text,
        )
        if ass_result and (ass_result[0] or ass_result[1]):
            return ass_result

    return split_bilingual(
        payload.get("sub_text"),
        payload.get("secondary_sub_text"),
        config.text,
    )

def result_to_json(result: CaptureResult) -> str:
    return json.dumps(
        {
            "ok": True,
            "japanese": result.japanese,
            "chinese": result.chinese,
            "clip": str(result.clip_path),
            "tsv": str(result.tsv_path),
            "manifest": str(result.manifest_path),
            "start": result.clip_window.start,
            "end": result.clip_window.end,
            "anki_note_id": result.anki.note_id if result.anki else None,
            "anki_error": result.anki_error,
        },
        ensure_ascii=True,
    )


def _resolve_media_path(payload: dict[str, Any]) -> Path | str:
    raw_path = payload.get("media_path") or payload.get("path")
    if not raw_path:
        raise ValueError("Payload does not include media_path")

    raw_path = str(raw_path)
    parsed = urlsplit(raw_path)
    if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
        return raw_path

    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        working_directory = payload.get("working_directory")
        if working_directory:
            path = Path(str(working_directory)).expanduser() / path

    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"Media file does not exist: {path}")
    return path


def _resolve_optional_path(value: object, working_directory: object = None) -> Path | None:
    if not value:
        return None
    path = Path(str(value)).expanduser()
    if not path.is_absolute() and working_directory:
        path = Path(str(working_directory)).expanduser() / path
    try:
        path = path.resolve()
    except OSError:
        return None
    if not path.exists():
        return None
    return path


def _sibling_subtitle_paths(media_path: Path) -> list[Path]:
    return [
        candidate
        for suffix in (".ass", ".ssa")
        if (candidate := media_path.with_suffix(suffix)).exists()
    ]


def _unique_existing_paths(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []
    for path in paths:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.exists():
            continue
        seen.add(resolved)
        result.append(resolved)
    return result


def _extract_clip(
    media_path: Path | str,
    clip_path: Path,
    window: ClipWindow,
    config: AppConfig,
) -> None:
    result = subprocess.run(
        _build_ffmpeg_command(media_path, clip_path, window, config),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            "ffmpeg failed while extracting the clip:\n"
            + (result.stderr.strip() or result.stdout.strip())
        )


def _build_ffmpeg_command(
    media_path: Path | str,
    clip_path: Path,
    window: ClipWindow,
    config: AppConfig,
) -> list[str]:
    cmd = [
        config.output.ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        _format_seconds(window.start),
        "-i",
        str(media_path),
        "-t",
        _format_seconds(window.length),
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-map_metadata",
        "-1",
        "-map_chapters",
        "-1",
        "-sn",
        "-dn",
    ]

    video_filter = _video_filter(config)
    if video_filter:
        cmd.extend(["-vf", video_filter])

    cmd.extend(["-c:v", config.output.video_codec])
    if config.output.video_codec.startswith("libvpx"):
        if config.output.video_deadline:
            cmd.extend(["-deadline", config.output.video_deadline])
        if config.output.video_cpu_used >= 0:
            cmd.extend(["-cpu-used", str(config.output.video_cpu_used)])
        if config.output.video_codec == "libvpx-vp9":
            cmd.extend(["-row-mt", "1"])
        cmd.extend(["-crf", str(config.output.video_crf), "-b:v", "0"])
    else:
        cmd.extend(["-crf", str(config.output.video_crf)])
        if config.output.video_preset:
            cmd.extend(["-preset", config.output.video_preset])

    cmd.extend(
        [
            "-pix_fmt",
            "yuv420p",
        ]
    )
    if config.output.audio_channels > 0:
        cmd.extend(["-ac", str(config.output.audio_channels)])
    cmd.extend(
        [
            "-c:a",
            config.output.audio_codec,
            "-b:a",
            config.output.audio_bitrate,
        ]
    )
    if clip_path.suffix.lower() == ".mp4":
        cmd.extend(["-movflags", "+faststart"])
    cmd.append(str(clip_path))
    return cmd


def _video_filter(config: AppConfig) -> str:
    filters: list[str] = []
    if config.output.video_max_height > 0:
        filters.append(
            f"scale=-2:{int(config.output.video_max_height)}:force_original_aspect_ratio=decrease"
        )
    if config.output.video_fps > 0:
        filters.append(f"fps={_format_filter_number(config.output.video_fps)}")
    return ",".join(filters)


def _format_filter_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def _should_append_tsv(config: AppConfig, anki_error: str | None) -> bool:
    return config.output.append_tsv or not config.anki.enabled or anki_error is not None


def _delete_file_if_exists(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _next_clip_path(
    output_root: Path,
    media_path: Path | str,
    window: ClipWindow,
    extension: str,
    media_title: object = None,
) -> Path:
    source = _slug(_media_stem(media_path, media_title))
    digest = hashlib.sha1(
        f"{media_path}|{window.start}|{window.end}".encode("utf-8")
    ).hexdigest()[:8]
    start_ms = int(window.start * 1000)
    stem = f"{datetime.now():%Y%m%d-%H%M%S}_{source}_{start_ms}ms_{digest}"
    extension = _safe_extension(extension)
    candidate = output_root / f"{stem}.{extension}"
    index = 2
    while candidate.exists():
        candidate = output_root / f"{stem}_{index}.{extension}"
        index += 1
    return candidate


def _append_tsv(path: Path, fields: list[str]) -> None:
    line = "\t".join(field.replace("\t", " ") for field in fields) + "\n"
    with path.open("a", encoding="utf-8", newline="") as file:
        file.write(line)


def _append_manifest(path: Path, data: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False) + "\n")


def _media_field(filename: str, reference_type: str) -> str:
    escaped = html.escape(filename, quote=True)
    if reference_type == "sound":
        return f"[sound:{escaped}]"
    return (
        f'<video id="anime-video" class="anime-video-player" src="{escaped}" '
        f'playsinline controls preload="metadata" data-repeat="15">'
        f'<source src="{escaped}">'
        "Your browser does not support the video tag."
        "</video>"
    )


def _field_html(text: str) -> str:
    return html.escape(text, quote=False).replace("\n", "<br>")


def _source_text(
    payload: dict[str, Any],
    media_path: Path | str,
    window: ClipWindow,
) -> str:
    title = payload.get("media_title") or _media_name(media_path)
    return f"{title} [{_format_seconds(window.start)} - {_format_seconds(window.end)}]"


def _media_stem(media_path: Path | str, media_title: object = None) -> str:
    if media_title:
        return Path(str(media_title)).stem
    return Path(_media_name(media_path)).stem


def _media_name(media_path: Path | str) -> str:
    if isinstance(media_path, Path):
        return media_path.name
    parsed = urlsplit(media_path)
    return Path(unquote(parsed.path)).name or "clip"



def _float_or_none(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_seconds(value: float) -> str:
    return f"{value:.3f}"


def _enforce_length(
    *,
    start: float,
    end: float,
    center: float,
    minimum: float,
    maximum: float,
    duration: float | None,
) -> tuple[float, float]:
    if end < start:
        end = start

    length = end - start
    if length < minimum:
        half = minimum / 2.0
        start = center - half
        end = center + half
    elif length > maximum:
        half = maximum / 2.0
        start = center - half
        end = center + half

    start = max(0.0, start)
    if duration is not None and end > duration:
        end = duration
        start = max(0.0, end - max(minimum, min(maximum, end - start)))

    if end - start < minimum:
        end = start + minimum
        if duration is not None and end > duration:
            end = duration

    return start, max(start, end)

def _safe_extension(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "", value.lstrip("."))
    return cleaned.lower() or "webm"

def _slug(value: str, max_length: int = 64) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", normalized)
    safe = safe.strip("._-")
    if not safe:
        safe = "clip"
    return safe[:max_length].strip("._-") or "clip"
