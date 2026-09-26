from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
import os
import textwrap
import tomllib
from typing import Any


@dataclass(frozen=True)
class OutputConfig:
    root: str = str(Path.home() / "AnimeAnki")
    tsv_name: str = "anki_import.tsv"
    manifest_name: str = "capture_manifest.jsonl"
    padding_before: float = 0.25
    padding_after: float = 0.35
    fallback_before: float = 1.0
    fallback_after: float = 2.0
    min_clip_seconds: float = 1.2
    max_clip_seconds: float = 12.0
    ffmpeg_path: str = "ffmpeg"
    clip_extension: str = "webm"
    video_codec: str = "libvpx-vp9"
    video_crf: int = 32
    video_preset: str = "veryfast"
    video_max_height: int = 360
    video_fps: float = 0.0
    video_deadline: str = "realtime"
    video_cpu_used: int = 8
    audio_codec: str = "libopus"
    audio_bitrate: str = "128k"
    audio_channels: int = 2
    media_reference: str = "video"
    keep_media: bool = True
    append_tsv: bool = True


@dataclass(frozen=True)
class TextConfig:
    split_mode: str = "auto"
    japanese_first: bool = True
    primary_subtitle_language: str = "japanese"


@dataclass(frozen=True)
class AnkiConfig:
    enabled: bool = False
    connect_url: str = "http://127.0.0.1:8765"
    deck: str = "Japanese::Anime"
    model: str = "Basic"
    japanese_field: str = "Front"
    chinese_field: str = "Back"
    clip_field: str = ""
    source_field: str = ""
    tags: tuple[str, ...] = ("anime", "mined")
    allow_duplicate: bool = False


@dataclass(frozen=True)
class AppConfig:
    output: OutputConfig = OutputConfig()
    text: TextConfig = TextConfig()
    anki: AnkiConfig = AnkiConfig()


def default_config_path() -> Path:
    explicit = os.environ.get("ANIME_TO_ANKI_CONFIG")
    if explicit:
        return Path(explicit).expanduser()

    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "anime-to-anki" / "config.toml"

    return Path.home() / ".config" / "anime-to-anki" / "config.toml"


def find_config_path(path: str | None = None) -> Path | None:
    if path:
        return Path(path).expanduser()

    env_path = os.environ.get("ANIME_TO_ANKI_CONFIG")
    if env_path:
        return Path(env_path).expanduser()

    cwd_config = Path.cwd() / "config.toml"
    if cwd_config.exists():
        return cwd_config

    default_path = default_config_path()
    if default_path.exists():
        return default_path

    return None


def load_config(path: str | None = None) -> AppConfig:
    config_path = find_config_path(path)
    if config_path is None:
        return AppConfig()

    with config_path.open("rb") as file:
        data = tomllib.load(file)

    return AppConfig(
        output=_coerce_dataclass(OutputConfig, data.get("output", {})),
        text=_coerce_dataclass(TextConfig, data.get("text", {})),
        anki=_coerce_anki(data.get("anki", {})),
    )


def resolved_output_root(config: AppConfig) -> Path:
    return Path(config.output.root).expanduser().resolve()


def sample_config() -> str:
    return textwrap.dedent(
        """\
        [output]
        # All captures are written here. Keep media files beside anki_import.tsv
        # if you plan to import the TSV manually into Anki.
        root = "~/AnimeAnki"
        tsv_name = "anki_import.tsv"
        manifest_name = "capture_manifest.jsonl"

        # If mpv exposes subtitle start/end times, the clip uses that subtitle
        # range plus this padding. Otherwise it falls back to time_pos +/- below.
        padding_before = 0.25
        padding_after = 0.35
        fallback_before = 1.0
        fallback_after = 2.0
        min_clip_seconds = 1.2
        max_clip_seconds = 12.0

        ffmpeg_path = "ffmpeg"
        # WebM is the safest video format for Anki Desktop video playback.
        clip_extension = "webm"
        video_codec = "libvpx-vp9"
        video_crf = 32
        video_preset = "veryfast"
        # Downscale video for faster captures and smaller Anki media.
        # Set to 0 to keep the original height.
        video_max_height = 360
        # Set above 0 to cap frame rate, e.g. 24.0.
        video_fps = 0.0
        # Fast WebM/VP9 options. Increase quality by using good/4 or realtime/6.
        video_deadline = "realtime"
        video_cpu_used = 8
        audio_codec = "libopus"
        audio_bitrate = "128k"
        # Downmix surround audio to stereo for smaller Anki clips and broad encoder support.
        # Set to 0 to keep the source channel count.
        audio_channels = 2

        # "video" writes <video controls src="..."></video>.
        # "sound" writes [sound:...] for people who prefer Anki's sound syntax.
        media_reference = "video"

        # If AnkiConnect import succeeds, false removes the local clip copy.
        keep_media = true
        # If false, TSV is written only when AnkiConnect is disabled or fails.
        append_tsv = true

        [text]
        # auto: if mpv provides secondary subtitles, use those as Chinese.
        # Otherwise split by line and simple language cues.
        # Use first_chinese when one bilingual subtitle track is ordered Chinese/Japanese.
        # Use first_japanese when it is ordered Japanese/Chinese.
        split_mode = "auto"
        japanese_first = true
        # For two mpv subtitle tracks: japanese means primary=Japanese, secondary=Chinese.
        # Set to chinese when primary=Chinese and secondary=Japanese.
        primary_subtitle_language = "japanese"

        [anki]
        # Set true after installing AnkiConnect and opening Anki.
        enabled = false
        connect_url = "http://127.0.0.1:8765"
        deck = "Japanese::Anime"
        model = "Basic"

        # Basic uses Front/Back. For a custom note type, set these to your fields,
        # e.g. Japanese, Chinese, Clip, Source.
        japanese_field = "Front"
        chinese_field = "Back"
        clip_field = ""
        source_field = ""
        tags = ["anime", "mined"]
        allow_duplicate = false
        """
    )


def write_sample_config(path: str | None = None, force: bool = False) -> Path:
    config_path = Path(path).expanduser() if path else default_config_path()
    if config_path.exists() and not force:
        raise FileExistsError(f"Config already exists: {config_path}")

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(sample_config(), encoding="utf-8")
    return config_path


def _coerce_dataclass(cls: type[Any], values: dict[str, Any]) -> Any:
    names = {field.name for field in fields(cls)}
    kwargs = {key: value for key, value in values.items() if key in names}
    return cls(**kwargs)


def _coerce_anki(values: dict[str, Any]) -> AnkiConfig:
    kwargs = {
        key: value
        for key, value in values.items()
        if key in {field.name for field in fields(AnkiConfig)}
    }
    tags = kwargs.get("tags")
    if isinstance(tags, list):
        kwargs["tags"] = tuple(str(tag) for tag in tags)
    return AnkiConfig(**kwargs)

