import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anime_to_anki.config import TextConfig
from anime_to_anki.text import clean_subtitle, normalize_japanese_text, split_bilingual


JP_NAME = "\u541b\u306e\u540d\u524d\u306f\uff1f"
ZH_NAME = "\u4f60\u7684\u540d\u5b57\u662f\uff1f"
JP_GO = "\u884c\u3053\u3046\u3002"
ZH_GO = "\u8d70\u5427\u3002"
JP_KANJI = "\u56fd\u6226\u7528\u9b54\u8853\u5175\u5668\u80b2\u6210\u6a5f\u95a2"
ZH_SIMPLIFIED = "\u56fd\u6218\u7528\u6cd5\u672f\u5175\u5668\u57f9\u80b2\u673a\u6784"
JP_KARAOKE_FULL = "\u3072\u3068\u3088\u3072\u3068\u3088\u306b\u4eba\u898b\u77e5\u308a"
ZH_KARAOKE_FULL = "\u6bcf\u5929\u6bcf\u5929\u90fd\u6015\u751f\u5f97\u4e0d\u5f97\u4e86"
JP_SIDE = "\u30e0\u30ea\u30e0\u30ea!"
ZH_SIDE = "\u4e0d\u884c\u4e0d\u884c!"


class TextTests(unittest.TestCase):
    def test_clean_subtitle_strips_ass_and_newline_codes(self):
        self.assertEqual(
            clean_subtitle(r"{\pos(10,20)}" + JP_NAME + r"\N" + ZH_NAME),
            JP_NAME + "\n" + ZH_NAME,
        )


    def test_normalize_japanese_text_converts_simplified_variants_and_digits(self):
        self.assertEqual(
            normalize_japanese_text(
                "\u3067\u3082 \u5352\u4e1a\u307e\u3067\u306b\uff12\u5e74\u304b\u304b\u308b\u3093\u3067\u3059\u3088\u306d"
            ),
            "\u3067\u3082 \u5352\u696d\u307e\u3067\u306b2\u5e74\u304b\u304b\u308b\u3093\u3067\u3059\u3088\u306d",
        )

    def test_normalize_japanese_text_converts_common_mixed_subtitle_chars(self):
        self.assertEqual(
            normalize_japanese_text("\u56fd\u6218\u7528\u6cd5\u672f\u5175\u5668\u57f9\u80b2\u673a\u6784"),
            "\u56fd\u6226\u7528\u6cd5\u8853\u5175\u5668\u57f9\u80b2\u6a5f\u69cb",
        )

    def test_split_bilingual_from_two_lines(self):
        japanese, chinese = split_bilingual(JP_NAME + "\n" + ZH_NAME)
        self.assertEqual(japanese, JP_NAME)
        self.assertEqual(chinese, ZH_NAME)

    def test_secondary_subtitle_wins(self):
        japanese, chinese = split_bilingual(JP_GO, ZH_GO)
        self.assertEqual(japanese, JP_GO)
        self.assertEqual(chinese, ZH_GO)

    def test_first_chinese_mode(self):
        japanese, chinese = split_bilingual(
            ZH_NAME + "\n" + JP_NAME,
            config=TextConfig(split_mode="first_chinese"),
        )
        self.assertEqual(japanese, JP_NAME)
        self.assertEqual(chinese, ZH_NAME)

    def test_first_chinese_mode_respects_clear_japanese_first_lines(self):
        japanese, chinese = split_bilingual(
            JP_GO + "\n" + ZH_GO,
            config=TextConfig(split_mode="first_chinese"),
        )
        self.assertEqual(japanese, JP_GO)
        self.assertEqual(chinese, ZH_GO)

    def test_first_chinese_mode_uses_simplified_cjk_cues(self):
        japanese, chinese = split_bilingual(
            JP_KANJI + "\n" + ZH_SIMPLIFIED,
            config=TextConfig(split_mode="first_chinese"),
        )
        self.assertEqual(japanese, JP_KANJI)
        self.assertEqual(chinese, ZH_SIMPLIFIED)

    def test_first_chinese_mode_beats_secondary_subtitle_when_primary_is_bilingual(self):
        japanese, chinese = split_bilingual(
            ZH_NAME + "\n" + JP_NAME,
            "secondary subtitle should not win here",
            config=TextConfig(split_mode="first_chinese", primary_subtitle_language="chinese"),
        )
        self.assertEqual(japanese, JP_NAME)
        self.assertEqual(chinese, ZH_NAME)

    def test_chinese_primary_can_have_multiple_lines_with_japanese_secondary(self):
        japanese, chinese = split_bilingual(
            "你必须\n马上离开",
            JP_GO,
            config=TextConfig(split_mode="first_chinese", primary_subtitle_language="chinese"),
        )

        self.assertEqual(japanese, JP_GO)
        self.assertEqual(chinese, "你必须\n马上离开")

    def test_japanese_first_false_means_chinese_line_comes_first(self):
        japanese, chinese = split_bilingual(
            "Chinese line\nJapanese line",
            config=TextConfig(japanese_first=False),
        )
        self.assertEqual(japanese, "Japanese line")
        self.assertEqual(chinese, "Chinese line")

    def test_primary_subtitle_can_be_chinese(self):
        japanese, chinese = split_bilingual(
            ZH_GO,
            JP_GO,
            config=TextConfig(primary_subtitle_language="chinese"),
        )
        self.assertEqual(japanese, JP_GO)
        self.assertEqual(chinese, ZH_GO)


    def test_clean_subtitle_collapses_progressive_embedded_lines(self):
        raw = "\n".join(
            [
                "\u6bcf\u5929",
                "\u6bcf\u5929\u6bcf\u5929",
                ZH_KARAOKE_FULL,
                "\u3072",
                "\u3072\u3068",
                JP_KARAOKE_FULL,
            ]
        )

        self.assertEqual(clean_subtitle(raw), f"{ZH_KARAOKE_FULL}\n{JP_KARAOKE_FULL}")

    def test_split_bilingual_collapses_embedded_karaoke_text(self):
        raw = "\n".join(
            [
                "\u6bcf\u5929",
                "\u6bcf\u5929\u6bcf\u5929",
                ZH_KARAOKE_FULL,
                ZH_SIDE,
                "\u3072",
                "\u3072\u3068",
                JP_KARAOKE_FULL,
                JP_SIDE,
            ]
        )

        japanese, chinese = split_bilingual(raw)

        self.assertEqual(japanese, f"{JP_KARAOKE_FULL}\n{JP_SIDE}")
        self.assertEqual(chinese, f"{ZH_KARAOKE_FULL}\n{ZH_SIDE}")
if __name__ == "__main__":
    unittest.main()