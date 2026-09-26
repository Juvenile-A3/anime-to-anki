from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .config import TextConfig
from .text import clean_subtitle


KANA_RE = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff]")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


@dataclass(frozen=True)
class AssDialogue:
    start: float
    end: float
    style: str
    text: str
    order: int


def extract_bilingual_from_ass(
    path: str | Path,
    *,
    time_pos: float | None,
    sub_start: float | None = None,
    sub_end: float | None = None,
    config: TextConfig | None = None,
) -> tuple[str, str] | None:
    cfg = config or TextConfig()
    dialogues = parse_ass_dialogues(Path(path))
    if not dialogues:
        return None

    candidates = _dialogues_at_time(dialogues, time_pos)
    if not candidates and sub_start is not None and sub_end is not None:
        candidates = _dialogues_matching_range(dialogues, sub_start, sub_end)
    if not candidates:
        return None

    japanese: list[str] = []
    chinese: list[str] = []
    unknown: list[str] = []

    for dialogue in sorted(candidates, key=lambda item: item.order):
        language = _language_for_dialogue(dialogue)
        if language == "japanese":
            japanese.append(dialogue.text)
        elif language == "chinese":
            chinese.append(dialogue.text)
        else:
            unknown.append(dialogue.text)

    if japanese or chinese:
        if unknown and not japanese and cfg.japanese_first:
            japanese.extend(unknown)
        elif unknown and not chinese:
            chinese.extend(unknown)
        return _join_unique(japanese), _join_unique(chinese)

    return None


def parse_ass_dialogues(path: Path) -> list[AssDialogue]:
    text = _read_subtitle_text(path)
    section = ""
    event_format: list[str] = []
    dialogues: list[AssDialogue] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped.lower()
            continue
        if section != "[events]":
            continue
        if stripped.lower().startswith("format:"):
            event_format = [
                part.strip().lower()
                for part in stripped.split(":", 1)[1].split(",")
            ]
            continue
        if not stripped.lower().startswith("dialogue:") or not event_format:
            continue

        raw = stripped.split(":", 1)[1].lstrip()
        parts = raw.split(",", len(event_format) - 1)
        if len(parts) != len(event_format):
            continue
        values = dict(zip(event_format, parts))
        text_value = clean_subtitle(values.get("text", ""))
        if not text_value:
            continue

        start = _parse_ass_time(values.get("start", ""))
        end = _parse_ass_time(values.get("end", ""))
        if start is None or end is None:
            continue

        dialogues.append(
            AssDialogue(
                start=start,
                end=end,
                style=values.get("style", "").strip(),
                text=text_value,
                order=len(dialogues),
            )
        )

    return dialogues


def _dialogues_at_time(
    dialogues: list[AssDialogue],
    time_pos: float | None,
    tolerance: float = 0.08,
) -> list[AssDialogue]:
    if time_pos is None:
        return []
    return [
        dialogue
        for dialogue in dialogues
        if dialogue.start - tolerance <= time_pos <= dialogue.end + tolerance
    ]


def _dialogues_matching_range(
    dialogues: list[AssDialogue],
    sub_start: float,
    sub_end: float,
    tolerance: float = 0.12,
) -> list[AssDialogue]:
    return [
        dialogue
        for dialogue in dialogues
        if abs(dialogue.start - sub_start) <= tolerance
        and abs(dialogue.end - sub_end) <= tolerance
    ]


def _language_for_dialogue(dialogue: AssDialogue) -> str | None:
    tokens = {
        token
        for token in re.split(r"[^a-z0-9]+", dialogue.style.lower())
        if token
    }
    if tokens & {"jp", "jpn", "ja", "japanese"}:
        return "japanese"
    if tokens & {"ch", "chi", "chs", "cht", "cn", "zh", "zhcn", "zhtw"}:
        return "chinese"
    if KANA_RE.search(dialogue.text):
        return "japanese"
    if CJK_RE.search(dialogue.text):
        return "chinese"
    return None


def _join_unique(values: list[str]) -> str:
    result = _collapse_progressive_lines(values)
    return "\n".join(result)


def _collapse_progressive_lines(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        for line in value.splitlines():
            line = line.strip()
            key = _dedupe_key(line)
            if line and key and key not in seen:
                seen.add(key)
                unique.append(line)

    if len(unique) < 3:
        return unique

    keys = [_dedupe_key(line) for line in unique]
    result: list[str] = []
    for index, line in enumerate(unique):
        key = keys[index]
        is_progressive_fragment = any(
            other_index != index
            and key
            and key in other_key
            and len(other_key) > len(key)
            for other_index, other_key in enumerate(keys)
        )
        if not is_progressive_fragment:
            result.append(line)
    return result


def _dedupe_key(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _parse_ass_time(value: str) -> float | None:
    match = re.fullmatch(r"(\d+):(\d{2}):(\d{2})(?:\.(\d{1,3}))?", value.strip())
    if not match:
        return None
    hours, minutes, seconds, fraction = match.groups()
    fraction = (fraction or "0").ljust(3, "0")[:3]
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(fraction) / 1000
    )


def _read_subtitle_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")
