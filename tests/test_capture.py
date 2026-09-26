import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anime_to_anki.capture import (
    ClipWindow,
    CaptureResult,
    _build_ffmpeg_command,
    _extract_subtitle_text,
    _media_field,
    _next_clip_path,
    _resolve_media_path,
    _should_append_tsv,
    _slug,
    compute_clip_window,
    result_to_json,
)
from anime_to_anki.config import AnkiConfig, AppConfig, OutputConfig, TextConfig


JP = "\u6559\u80b2\u3057\u6226\u4e89\u306b\u99c6\u308a\u51fa\u3059\u5b64\u5150\u9662"
ZH = "\u6559\u80b2\u4ed6\u4eec \u5c06\u4ed6\u4eec\u9001\u4e0a\u6218\u573a\u7684\u5b64\u513f\u9662"


class ClipWindowTests(unittest.TestCase):
    def test_uses_subtitle_window_with_padding(self):
        config = AppConfig(output=OutputConfig(padding_before=0.2, padding_after=0.3))
        window = compute_clip_window(
            {"time_pos": 10, "sub_start": 9.5, "sub_end": 11.0, "duration": 20},
            config,
        )
        self.assertEqual(window.start, 9.3)
        self.assertEqual(window.end, 11.3)

    def test_fallback_window_when_subtitle_times_are_missing(self):
        config = AppConfig(output=OutputConfig(fallback_before=1.0, fallback_after=2.0))
        window = compute_clip_window({"time_pos": 10, "duration": 20}, config)
        self.assertEqual(window.start, 9.0)
        self.assertEqual(window.end, 12.0)

    def test_video_media_field_contains_video_tag_for_anki_media_detection(self):
        value = _media_field("clip.webm", "video")
        self.assertIn('<video', value)
        self.assertIn('src="clip.webm"', value)

    def test_sound_media_field_keeps_anki_sound_syntax(self):
        self.assertEqual(_media_field("clip.mp4", "sound"), "[sound:clip.mp4]")

    def test_result_json_is_ascii_safe_for_windows_mpv_subprocess(self):
        value = result_to_json(
            CaptureResult(
                japanese="僕は⸺",
                chinese="中文",
                clip_path=Path("clip.webm"),
                tsv_path=Path("anki_import.tsv"),
                manifest_path=Path("capture_manifest.jsonl"),
                clip_window=ClipWindow(1.0, 2.0),
                anki=None,
            )
        )

        value.encode("ascii")
        self.assertIn("\\u2e3a", value)

    def test_slug_keeps_media_filenames_ascii_safe(self):
        self.assertEqual(
            _slug("[Nekomoe kissaten&VCB-Studio] Medalist 01"),
            "Nekomoe_kissaten_VCB-Studio_Medalist_01",
        )

    def test_http_media_source_is_preserved_for_ffmpeg(self):
        media_url = (
            "http://127.0.0.1:7789/api/file"
            "?filename=RDovQW5pbWUvZXBpc29kZS5ta3Y%3D"
        )
        self.assertEqual(_resolve_media_path({"media_path": media_url}), media_url)

    def test_proxy_media_source_uses_mpv_title_for_clip_name(self):
        path = _next_clip_path(
            Path("output"),
            "http://127.0.0.1:7789/api/file?filename=encoded",
            ClipWindow(117.0, 120.0),
            "webm",
            media_title="[Group] Episode 04.mkv",
        )
        self.assertIn("Group_Episode_04", path.name)


    def test_ffmpeg_command_scales_and_uses_fast_vp9_options(self):
        config = AppConfig(
            output=OutputConfig(
                ffmpeg_path="ffmpeg",
                video_max_height=360,
                video_fps=24.0,
                video_deadline="realtime",
                video_cpu_used=8,
            )
        )
        cmd = _build_ffmpeg_command(
            Path("input.mkv"),
            Path("output.webm"),
            ClipWindow(1.0, 4.0),
            config,
        )

        self.assertIn("-vf", cmd)
        self.assertIn("scale=-2:360:force_original_aspect_ratio=decrease,fps=24", cmd)
        self.assertIn("-deadline", cmd)
        self.assertIn("realtime", cmd)
        self.assertIn("-cpu-used", cmd)
        self.assertIn("8", cmd)
        self.assertIn("-row-mt", cmd)
        self.assertIn("-ac", cmd)
        self.assertEqual(cmd[cmd.index("-ac") + 1], "2")

    def test_tsv_is_skipped_when_anki_import_succeeds_and_append_tsv_is_false(self):
        config = AppConfig(
            output=OutputConfig(append_tsv=False),
            anki=AnkiConfig(enabled=True),
        )
        self.assertFalse(_should_append_tsv(config, None))
        self.assertTrue(_should_append_tsv(config, "Anki is closed"))

    def test_sibling_ass_beats_forced_text_line_order(self):
        content = f"""[Script Info]
Title: test

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:03.00,Line JP - A,,0,0,0,,{JP}
Dialogue: 1,0:00:01.00,0:00:03.00,Line CN - A,,0,0,0,,{ZH}
"""
        config = AppConfig(text=TextConfig(split_mode="first_chinese"))
        with tempfile.TemporaryDirectory() as directory:
            media_path = Path(directory) / "episode.mkv"
            media_path.write_bytes(b"")
            media_path.with_suffix(".ass").write_text(content, encoding="utf-8")

            japanese, chinese = _extract_subtitle_text(
                {"time_pos": 2.0, "sub_text": f"{JP}\n{ZH}"},
                config,
                media_path,
            )

        self.assertEqual(japanese, JP)
        self.assertEqual(chinese, ZH)


if __name__ == "__main__":
    unittest.main()
