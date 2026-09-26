"""Create Anki song clips from local audio and SRT; never modifies originals or Anki.

python music_to_anki.py --manifest recovery_sources.json --output recovered
python music_to_anki.py --audio song.mp3 --japanese ja.srt --chinese zh.srt --output out
Requires Python 3.10+, ffmpeg and ffprobe on PATH. Only the standard library is used.
"""
import argparse
import concurrent.futures
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import unicodedata

FIELDS = ['ID', 'Reading', 'Audio_Sentence', 'Screenshot', 'Expression', 'Chinese',
          'Video', 'Audio_Extra', 'Notes', 'Definition', 'Morph', 'Artist', 'SongTitle', 'Album', 'Source']
TIMING = re.compile(r'(\d+):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d+):(\d{2}):(\d{2})[,.](\d{3})')
CREDITS = re.compile(r'^(?:作[词詞曲]|编曲|編曲|词|詞|曲|制作人|製作人|演唱|歌手|混音|录音|錄音|监制|出品|发行|Lyrics\s+by|Composed\s+by|Arranged\s+by|Produced\s+by)\s*[:：]', re.I)


def normalized(text):
    return re.sub(r'[^\w]', '', unicodedata.normalize('NFKC', text)).casefold()


def title_credit(cue, title, artist):
    if cue['start'] >= 15:
        return False
    text, title = normalized(cue['text']), normalized(title)
    return bool(title) and (text == title or
        (' - ' in cue['text'] and (text.startswith(title) or text.startswith(normalized(artist)))))


def run(args):
    p = subprocess.run(args, capture_output=True, timeout=180)
    if p.returncode:
        raise RuntimeError(f'{args[0]} failed ({p.returncode}): {p.stderr.decode("utf-8", errors="replace")[-4000:]}')
    return p.stdout


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)]))


def seconds(parts):
    h, m, s, ms = map(int, parts)
    if m >= 60 or s >= 60:
        raise ValueError('Invalid timestamp')
    return h * 3600 + m * 60 + s + ms / 1000


def read_srt(path):
    result = []
    for block in re.split(r'\n\s*\n', Path(path).read_text(encoding='utf-8-sig').replace('\r', '').strip()):
        match = TIMING.search(block)
        if not match:
            if block.strip(): raise ValueError(f'Invalid SRT block: {path}: {block[:100]}')
            continue
        start, end = seconds(match.groups()[:4]), seconds(match.groups()[4:])
        text = block[match.end():].strip()
        if end <= start:
            raise ValueError(f'Invalid cue range: {path}: {start}, {end}')
        result.append({'start': start, 'end': end, 'text': text})
    return result


def align(cue, translations):
    exact = [c for c in translations if abs(c['start']-cue['start']) < .002 and abs(c['end']-cue['end']) < .002]
    if exact:
        return '\n'.join(c['text'] for c in exact), 'exact'
    scored = []
    for c in translations:
        overlap = min(c['end'], cue['end'])-max(c['start'], cue['start'])
        if overlap > 0:
            scored.append((overlap, c))
    if not scored: return '', 'missing'
    overlap, best = max(scored, key=lambda pair: pair[0])
    # A neighboring translation must cover a substantial part of both cues.
    if overlap / max(best['end']-best['start'], cue['end']-cue['start']) < .5:
        return '', 'missing'
    return best['text'], 'overlap_review'


def prepare(source, output):
    audio = Path(source['audio']).resolve()
    info = probe(audio)
    stream = next(s for s in info['streams'] if s['codec_type'] == 'audio')
    duration = float(stream.get('duration', info['format']['duration']))
    tags = {k.lower(): v for k, v in info['format'].get('tags', {}).items()}
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()[:20]
    ja = read_srt(source['japanese'])
    zh = read_srt(source['chinese']) if source.get('chinese') else []
    cover = ''
    attached = next((s for s in info['streams'] if s.get('disposition', {}).get('attached_pic')), None)
    if attached:
        extension = '.png' if attached['codec_name'] == 'png' else '.jpg'
        cover = f'recovered_cover_{digest}{extension}'
        path = output / 'media' / cover
        if not path.exists():
            run(['ffmpeg', '-v', 'error', '-n', '-i', str(audio), '-map', f'0:{attached["index"]}', '-c', 'copy', '-frames:v', '1', str(path)])
    clips, skipped = [], []
    for i, cue in enumerate(ja, 1):
        text = cue['text']
        translation, alignment = align(cue, zh)
        reason = None
        if not text: reason = 'empty_original'
        elif CREDITS.search(text): reason = 'credit'
        elif '享有本翻译作品的著作权' in translation or '享有本翻译作品的著作权' in text: reason = 'title_or_copyright'
        elif title_credit(cue, tags.get('title', ''), tags.get('artist', '')): reason = 'title_or_copyright'
        elif cue['start'] >= duration: reason = 'starts_after_audio'
        if reason:
            skipped.append(dict(cue, reason=reason)); continue
        start, end = max(0, cue['start']-.25), min(duration, cue['end']+.25)
        if end-start < .1:
            skipped.append(dict(cue, reason='too_short')); continue
        ident = f'recovered_{digest}_{round(start*1000):08d}_{round(end*1000):08d}_{i:04d}'
        clips.append(dict(id=ident, filename=ident+'.mp3', audio=str(audio), start=start, end=end,
                          japanese=text, chinese=translation, alignment=alignment,
                          original_index=i, cover=cover, artist=tags.get('artist', ''),
                          title=tags.get('title', audio.stem), album=tags.get('album', ''),
                          end_clamped=cue['end']+.25 > duration))
    return clips, dict(source=source, tags={k: tags.get(k, '') for k in ('title','artist','album')},
                       duration=duration, clips=len(clips), skipped=skipped,
                       translation_review=sum(not c['chinese'] or c['alignment']!='exact' for c in clips))


def render(clip, media):
    destination = media / clip['filename']
    duration = clip['end']-clip['start']
    if not destination.exists():
        temporary = destination.with_suffix('.part.mp3')
        # Explicitly select audio, remove image streams and inherited metadata,
        # and re-encode once. Never use legacy TagLib or mp3gain on the result.
        run(['ffmpeg', '-v', 'error', '-xerror', '-y', '-ss', f'{clip["start"]:.3f}', '-i', clip['audio'],
             '-t', f'{duration:.3f}', '-map', '0:a:0', '-vn', '-sn', '-dn', '-map_metadata', '-1',
             '-af', f'volume={clip.get("gain_db", 0):.3f}dB',
             '-c:a', 'libmp3lame', '-b:a', '192k', '-ar', '44100', '-ac', '2', '-threads', '1',
             '-id3v2_version', '3', '-metadata', 'title='+clip['title'],
             '-metadata', 'artist='+clip['artist'], '-metadata', 'album='+clip['album'], str(temporary)])
        validate(temporary, duration)
        temporary.rename(destination)
    else:
        validate(destination, duration)
    return dict(id=clip['id'], bytes=destination.stat().st_size, expected_seconds=duration, validated=True)


def validate(path, duration):
    info = probe(path)
    if len(info['streams']) != 1 or info['streams'][0].get('codec_name') != 'mp3':
        raise ValueError(f'Unexpected media streams: {path}')
    pcm = run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path), '-map', '0:a:0',
               '-f', 's16le', '-ar', '44100', '-ac', '2', '-'])
    actual = len(pcm) / (44100*2*2)
    if not pcm or not math.isclose(actual, duration, abs_tol=.08):
        raise ValueError(f'Decoded duration mismatch: {path}: expected {duration}, got {actual}')


def clean(value):
    return html.escape(value).replace('\n', '<br>')


def export_tsv(clips, output, deck='Japanese::Music'):
    with (output / 'music_import.tsv').open('w', encoding='utf-8', newline='') as stream:
        stream.write('#separator:Tab\n#html:true\n#notetype:subs2srs+\n#deck column:16\n#tags:music\n')
        stream.write('#columns:'+'\t'.join(FIELDS+['Deck'])+'\n')
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        for c in clips:
            fields = dict.fromkeys(FIELDS, '')
            fields.update(ID=c['id'], Audio_Sentence=f'[sound:{c["filename"]}]',
                          Screenshot=f'<img src="{c["cover"]}">' if c['cover'] else '',
                          Expression=clean(c['japanese']), Chinese=clean(c['chinese']),
                          Artist=clean(c['artist']), SongTitle=clean(c['title']), Album=clean(c['album']))
            fields['Notes'] = '由原曲及 SRT 生成。'
            if not c['chinese']: fields['Notes'] += ' 原字幕缺少可匹配的翻译。'
            elif c['alignment'] != 'exact': fields['Notes'] += ' 翻译按时间重叠匹配，需复核。'
            if c['end']-c['start'] > 15: fields['Notes'] += ' 原字幕跨度超过 15 秒，可能包含间奏或尾奏，需复核。'
            writer.writerow([fields[k] for k in FIELDS]+[deck])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--audio', type=Path)
    parser.add_argument('--japanese', type=Path)
    parser.add_argument('--chinese', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--deck', default='Japanese::Music', help='Anki destination deck')
    args = parser.parse_args()
    if args.manifest:
        sources = json.loads(args.manifest.read_text(encoding='utf-8'))
        for source in sources:
            for key in ('audio', 'japanese', 'chinese'):
                if source.get(key):
                    path = Path(source[key]).expanduser()
                    source[key] = str(path if path.is_absolute() else args.manifest.resolve().parent / path)
    elif args.audio and args.japanese:
        sources = [dict(audio=str(args.audio), japanese=str(args.japanese), chinese=str(args.chinese) if args.chinese else None)]
    else:
        parser.error('Supply --manifest or --audio and --japanese')
    output = args.output.resolve()
    media = output / 'media'
    media.mkdir(parents=True, exist_ok=True)
    clips, songs, preparation_errors = [], [], []
    for source in sources:
        try:
            song_clips, song = prepare(source, output)
            if not song_clips:
                raise ValueError('No usable lyric cues')
            clips.extend(song_clips); songs.append(song)
        except (ValueError, OSError, StopIteration, RuntimeError) as error:
            preparation_errors.append(dict(source=source, error=str(error)))
            print(f'Skipped source requiring attention: {source["audio"]}: {error}', flush=True)
    (output / 'preparation_errors.json').write_text(json.dumps(preparation_errors, ensure_ascii=False, indent=2), encoding='utf-8')
    if not clips:
        raise RuntimeError('No usable songs; see preparation_errors.json')
    if len({c['filename'] for c in clips}) != len(clips):
        raise ValueError('Duplicate sources or media names')
    (output / 'manifest.json').write_text(json.dumps(dict(songs=songs, clips=clips), ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Prepared {len(songs)} songs, {len(clips)} clips', flush=True)
    checks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for result in pool.map(lambda c: render(c, media), clips):
            checks.append(result)
            if len(checks) % 100 == 0: print(f'Validated {len(checks)}/{len(clips)}', flush=True)
    (output / 'validation.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
    media_names = {c['filename'] for c in clips} | {c['cover'] for c in clips if c['cover']}
    hashes = {name: hashlib.sha256((media/name).read_bytes()).hexdigest() for name in sorted(media_names)}
    (output / 'checksums.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    installer = Path(__file__).resolve().parent/'install_media.py'
    if installer.exists() and installer.resolve() != (output/installer.name).resolve():
        shutil.copy2(installer, output/installer.name)
    export_tsv(clips, output, args.deck)
    with (output / '需要复核的翻译.tsv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t')
        writer.writerow(['Song', 'Artist', 'Start', 'Japanese', 'Chinese', 'Reason', 'ID'])
        for c in clips:
            if not c['chinese'] or c['alignment']!='exact':
                writer.writerow([c['title'], c['artist'], c['start'], c['japanese'], c['chinese'], 'missing' if not c['chinese'] else c['alignment'], c['id']])
    with (output / '需要复核的长切片.tsv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t')
        writer.writerow(['Song', 'Start', 'Duration', 'Japanese', 'ID'])
        for c in clips:
            if c['end']-c['start'] > 15:
                writer.writerow([c['title'], c['start'], round(c['end']-c['start'],3), c['japanese'], c['id']])
    print(f'Done: {len(checks)} validated clips; {output}', flush=True)
    if preparation_errors:
        print(f'Attention: {len(preparation_errors)} sources were not exported; see preparation_errors.json', flush=True)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
