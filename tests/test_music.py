import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'music_to_anki', Path(__file__).resolve().parents[1] / 'tools/music/music_to_anki.py')
music = importlib.util.module_from_spec(spec)
spec.loader.exec_module(music)


class MusicTests(unittest.TestCase):
    def test_srt_accepts_bom_and_multiline_but_rejects_reversed_time(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'lyrics.srt'
            path.write_text('1\n00:00:01,000 --> 00:00:02,500\nこんにちは\n世界\n', encoding='utf-8-sig')
            self.assertEqual(music.read_srt(path), [{'start': 1.0, 'end': 2.5, 'text': 'こんにちは\n世界'}])
            path.write_text('1\n00:00:02,500 --> 00:00:01,000\n逆転\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                music.read_srt(path)

    def test_alignment_does_not_choose_brief_neighbor_overlap(self):
        cue = {'start': 10, 'end': 12, 'text': '原文'}
        self.assertEqual(music.align(cue, [{'start': 8, 'end': 10.2, 'text': '邻句'}]), ('', 'missing'))
        self.assertEqual(music.align(cue, [{'start': 10.1, 'end': 12.1, 'text': '译文'}]), ('译文', 'overlap_review'))
        self.assertEqual(music.align(cue, [{'start': 10, 'end': 12, 'text': '译文'}]), ('译文', 'exact'))

    def test_export_preserves_requested_deck_and_escapes_html(self):
        clip = dict(id='unit', filename='unit.mp3', cover='', japanese='<歌詞>', chinese='中文',
                    artist='トゲナシトゲアリ', title='曲名', album='', alignment='exact', start=0, end=2)
        with tempfile.TemporaryDirectory() as folder:
            music.export_tsv([clip], Path(folder), 'Examples::Music')
            lines = (Path(folder) / 'music_import.tsv').read_text(encoding='utf-8').splitlines()
            rows = list(csv.reader((line for line in lines if not line.startswith('#')), delimiter='\t'))
            self.assertEqual(len(rows[0]), 16)
            self.assertEqual(rows[0][-1], 'Examples::Music')
            self.assertEqual(rows[0][music.FIELDS.index('Expression')], '&lt;歌詞&gt;')


if __name__ == '__main__':
    unittest.main()
