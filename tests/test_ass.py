import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anime_to_anki.ass import extract_bilingual_from_ass


JP = "\u6c37\u306e\u4e0a"
ZH = "\u51b0\u9762\u4e4b\u4e0a"
JP_KARAOKE_FULL = "\u3072\u3068\u3088\u3072\u3068\u3088\u306b\u4eba\u898b\u77e5\u308a"
ZH_KARAOKE_FULL = "\u6bcf\u5929\u6bcf\u5929\u90fd\u6015\u751f\u5f97\u4e0d\u5f97\u4e86"
JP_SIDE = "\u30e0\u30ea\u30e0\u30ea!"
ZH_SIDE = "\u4e0d\u884c\u4e0d\u884c!"


class AssTests(unittest.TestCase):
    def test_extracts_bilingual_lines_by_ass_style_at_time(self):
        content = f"""[Script Info]
Title: test

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 5,0:00:11.77,0:00:13.00,Dial_JP,,0,0,0,,{JP}
Dialogue: 6,0:00:11.77,0:00:13.00,Dial_CH,,0,0,0,,{ZH}
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.ass"
            path.write_text(content, encoding="utf-8")

            japanese, chinese = extract_bilingual_from_ass(path, time_pos=12.0)

        self.assertEqual(japanese, JP)
        self.assertEqual(chinese, ZH)

    def test_collapses_progressive_karaoke_lines_at_time(self):
        content = f"""[Script Info]
Title: karaoke

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.46,0:00:04.17,OP JP,,0,0,0,,\u3072
Dialogue: 0,0:00:01.58,0:00:04.17,OP JP,,0,0,0,,\u3072\u3068
Dialogue: 0,0:00:01.70,0:00:04.17,OP JP,,0,0,0,,{JP_KARAOKE_FULL}
Dialogue: 0,0:00:01.46,0:00:04.17,OP JP \u5074,,0,0,0,,{JP_SIDE}
Dialogue: 0,0:00:01.46,0:00:04.17,OP CN,,0,0,0,,\u6bcf\u5929
Dialogue: 0,0:00:01.58,0:00:04.17,OP CN,,0,0,0,,\u6bcf\u5929\u6bcf\u5929
Dialogue: 0,0:00:01.70,0:00:04.17,OP CN,,0,0,0,,{ZH_KARAOKE_FULL}
Dialogue: 0,0:00:01.46,0:00:04.17,OP CN \u4fa7,,0,0,0,,{ZH_SIDE}
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.ass"
            path.write_text(content, encoding="utf-8")

            japanese, chinese = extract_bilingual_from_ass(path, time_pos=2.8)

        self.assertEqual(japanese, f"{JP_KARAOKE_FULL}\n{JP_SIDE}")
        self.assertEqual(chinese, f"{ZH_KARAOKE_FULL}\n{ZH_SIDE}")


if __name__ == "__main__":
    unittest.main()