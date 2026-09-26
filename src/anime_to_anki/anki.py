from __future__ import annotations

import base64
from dataclasses import dataclass
import json
from pathlib import Path
import urllib.error
import urllib.request

from .config import AnkiConfig


@dataclass(frozen=True)
class AnkiConnectResult:
    note_id: int | None
    stored_media: bool


@dataclass(frozen=True)
class ModelInstallResult:
    model_name: str
    status: str


def add_note_via_ankiconnect(
    *,
    config: AnkiConfig,
    japanese_html: str,
    chinese_html: str,
    media_html: str,
    source_html: str,
    media_path: Path,
) -> AnkiConnectResult:
    media_data = base64.b64encode(media_path.read_bytes()).decode("ascii")
    _request(
        config,
        "storeMediaFile",
        {
            "filename": media_path.name,
            "data": media_data,
            "deleteExisting": True,
        },
    )

    fields: dict[str, str] = {}
    if config.model == "subs2srs+":
        # The unified type sorts and checks duplicates by its ID field.
        fields["ID"] = "anime_" + media_path.stem
    fields[config.japanese_field] = japanese_html
    fields[config.chinese_field] = chinese_html

    if config.clip_field:
        fields[config.clip_field] = media_html
    else:
        fields[config.japanese_field] = _join_html(fields[config.japanese_field], media_html)

    if config.source_field:
        fields[config.source_field] = source_html
    else:
        fields[config.chinese_field] = _join_html(fields[config.chinese_field], source_html)

    note = {
        "deckName": config.deck,
        "modelName": config.model,
        "fields": fields,
        "tags": list(config.tags),
        "options": {
            "allowDuplicate": config.allow_duplicate,
            "duplicateScope": "deck",
        },
    }
    note_id = _request(config, "addNote", {"note": note})
    return AnkiConnectResult(note_id=note_id, stored_media=True)


def check_ankiconnect(config: AnkiConfig) -> int:
    version = _request(config, "version", {})
    return int(version)


def install_or_update_model(
    *,
    config: AnkiConfig,
    model_name: str,
    fields: list[str],
    card_name: str,
    front: str,
    back: str,
    css: str,
) -> ModelInstallResult:
    model_names = _request(config, "modelNames", {})
    if model_name in model_names:
        existing_fields = _request(config, "modelFieldNames", {"modelName": model_name})
        missing = [field for field in fields if field not in existing_fields]
        if missing:
            raise RuntimeError(
                f"Existing model {model_name!r} is missing fields: {', '.join(missing)}"
            )

        _request(
            config,
            "updateModelTemplates",
            {
                "model": {
                    "name": model_name,
                    "templates": {card_name: {"Front": front, "Back": back}},
                }
            },
        )
        _request(
            config,
            "updateModelStyling",
            {"model": {"name": model_name, "css": css}},
        )
        return ModelInstallResult(model_name=model_name, status="updated")

    _request(
        config,
        "createModel",
        {
            "modelName": model_name,
            "inOrderFields": fields,
            "css": css,
            "isCloze": False,
            "cardTemplates": [{"Name": card_name, "Front": front, "Back": back}],
        },
    )
    return ModelInstallResult(model_name=model_name, status="created")


def _request(config: AnkiConfig, action: str, params: dict) -> object:
    payload = json.dumps(
        {"action": action, "version": 6, "params": params},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        config.connect_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach AnkiConnect at {config.connect_url}: {exc}") from exc

    data = json.loads(raw)
    if data.get("error"):
        raise RuntimeError(f"AnkiConnect {action} failed: {data['error']}")
    return data.get("result")


def _join_html(first: str, second: str) -> str:
    if not first:
        return second
    if not second:
        return first
    return f"{first}<br>{second}"
