from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

from .anki import check_ankiconnect, install_or_update_model
from .capture import (
    capture_from_payload,
    load_payload_file,
    load_payload_json,
    result_to_json,
)
from .config import load_config, resolved_output_root, write_sample_config


MODEL_FIELDS = ["ID", "Reading", "Audio_Sentence", "Screenshot", "Expression", "Chinese",
                "Video", "Audio_Extra", "Notes", "Definition", "Morph", "Artist", "SongTitle", "Album", "Source"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="anime-to-anki")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-config", help="write a sample config")
    init_parser.add_argument("--path", help="where to write config.toml")
    init_parser.add_argument("--force", action="store_true", help="overwrite existing config")

    capture_parser = subparsers.add_parser("capture", help="capture one note from an mpv payload")
    capture_parser.add_argument("--config", help="config.toml path")
    payload_group = capture_parser.add_mutually_exclusive_group(required=True)
    payload_group.add_argument("--payload-file", help="JSON payload written by the mpv script")
    payload_group.add_argument("--payload-json", help="JSON payload string")

    doctor_parser = subparsers.add_parser("doctor", help="check local setup")
    doctor_parser.add_argument("--config", help="config.toml path")

    model_parser = subparsers.add_parser(
        "install-model",
        help="create or update the unified audio/video Anki note type via AnkiConnect",
    )
    model_parser.add_argument("--config", help="config.toml path")
    model_parser.add_argument("--name", default="subs2srs+", help="Anki note type name")
    model_parser.add_argument("--card-name", default="Card 1", help="card template name")
    model_parser.add_argument(
        "--template-dir",
        default=str(_default_model_dir()),
        help="folder containing front.html, back.html and style.css",
    )

    args = parser.parse_args(argv)

    try:
        if args.command == "init-config":
            path = write_sample_config(args.path, force=args.force)
            print(f"Wrote config: {path}")
            return 0

        if args.command == "capture":
            config = load_config(args.config)
            payload = (
                load_payload_file(args.payload_file)
                if args.payload_file
                else load_payload_json(args.payload_json)
            )
            result = capture_from_payload(payload, config)
            print(result_to_json(result))
            return 0

        if args.command == "doctor":
            return _doctor(args.config)

        if args.command == "install-model":
            return _install_model(args)

    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1

    return 2


def _doctor(config_path: str | None) -> int:
    config = load_config(config_path)
    output_root = resolved_output_root(config)
    ffmpeg = shutil.which(config.output.ffmpeg_path)

    print(f"Output folder: {output_root}")
    print(f"ffmpeg: {ffmpeg or 'NOT FOUND'}")

    if config.anki.enabled:
        try:
            version = check_ankiconnect(config.anki)
            print(f"AnkiConnect: OK (version {version})")
        except Exception as exc:
            print(f"AnkiConnect: FAILED ({exc})")
            return 1
    else:
        print("AnkiConnect: disabled")

    return 0 if ffmpeg else 1


def _install_model(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    template_dir = Path(args.template_dir).expanduser().resolve()
    front = (template_dir / "front.html").read_text(encoding="utf-8")
    back = (template_dir / "back.html").read_text(encoding="utf-8")
    css = (template_dir / "style.css").read_text(encoding="utf-8")

    result = install_or_update_model(
        config=config.anki,
        model_name=args.name,
        fields=MODEL_FIELDS,
        card_name=args.card_name,
        front=front,
        back=back,
        css=css,
    )
    print(f"Anki model {result.status}: {result.model_name}")
    print("Fields: " + ", ".join(MODEL_FIELDS))
    return 0


def _default_model_dir() -> Path:
    project_model = Path(__file__).resolve().parents[2] / "model" / "subs2srs-plus"
    if project_model.exists():
        return project_model
    cwd_model = Path.cwd() / "model" / "subs2srs-plus"
    return cwd_model
