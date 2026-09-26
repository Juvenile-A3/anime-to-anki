"""Export selected notes via read-only AnkiConnect calls, without scheduling.

Requires: pip install genanki
Outputs: cards.apkg, cards.tsv, cards.json, media/ and checksums.json.
"""
import argparse
import base64
import csv
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.request

FIELDS = ['ID', 'Reading', 'Audio_Sentence', 'Screenshot', 'Expression', 'Chinese',
          'Video', 'Audio_Extra', 'Notes', 'Definition', 'Morph', 'Artist', 'SongTitle', 'Album', 'Source']
PUBLIC_FIELDS = {'Reading', 'Audio_Sentence', 'Screenshot', 'Expression', 'Chinese',
                 'Video', 'Artist', 'SongTitle', 'Album', 'Source'}
MEDIA = re.compile(r'\[sound:([^\]]+)\]|(?:src)=["\']([^"\']+)["\']')


def ac(action, **params):
    req = urllib.request.Request('http://127.0.0.1:8765',
        json.dumps(dict(action=action, version=6, params=params)).encode(),
        {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = json.load(response)
    if data['error']:
        raise RuntimeError(data['error'])
    return data['result']


def main():
    import genanki
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query', required=True, help='Anki search query')
    parser.add_argument('--limit', type=int, help='Maximum notes; omit to export all matches')
    parser.add_argument('--slug', required=True, help='ASCII namespace for exported IDs')
    parser.add_argument('--deck', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9-]+', args.slug):
        parser.error('--slug must contain lowercase ASCII letters, digits or hyphens')
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    if args.output.exists():
        parser.error('Use a new output directory to avoid stale media or accidental overwrite')
    ids = sorted(ac('findNotes', query=args.query))
    if args.limit:
        ids = ids[:args.limit]
    if not ids:
        parser.error('No matching notes')
    notes = ac('notesInfo', notes=ids)
    if any(n['modelName'] != 'subs2srs+' for n in notes):
        parser.error('This exporter expects the subs2srs+ note type')
    args.output.mkdir(parents=True)
    media = args.output / 'media'
    media.mkdir()
    records, hashes, renamed = [], {}, {}
    for index, note in enumerate(notes, 1):
        fields = {k: note['fields'].get(k, {}).get('value', '') if k in PUBLIC_FIELDS else '' for k in FIELDS}
        fields['ID'] = f'example_{args.slug}_{index:04d}'
        # Notes, tags, original IDs and all review/scheduling data are omitted.
        for key, value in fields.items():
            if re.search(r'[A-Za-z]:[\\/]|file://|/(?:home|Users)/', html.unescape(value)):
                raise ValueError(f'Local path in exported field {key}; clean the export source first')
            for match in list(MEDIA.finditer(value)):
                old = html.unescape(match.group(1) or match.group(2))
                if '/' in old or '\\' in old or ':' in old:
                    raise ValueError('Expected a local Anki media filename')
                if old not in renamed:
                    raw = ac('retrieveMediaFile', filename=old)
                    if not raw:
                        raise FileNotFoundError(old)
                    content = base64.b64decode(raw, validate=True)
                    digest = hashlib.sha256(content).hexdigest()
                    name = f'{args.slug}_{digest[:20]}{Path(old).suffix.lower()}'
                    (media/name).write_bytes(content)
                    hashes[name] = digest
                    renamed[old] = name
                value = value.replace(match.group(1) or match.group(2), renamed[old])
            fields[key] = value
        records.append(fields)
    root = Path(__file__).resolve().parents[1]
    template = root/'model'/'subs2srs-plus'
    model = genanki.Model(1732610917, 'Anime to Anki Examples',
        fields=[{'name': f} for f in FIELDS],
        templates=[{'name': 'Card 1', 'qfmt': (template/'front.html').read_text(encoding='utf-8'),
                    'afmt': (template/'back.html').read_text(encoding='utf-8')}],
        css=(template/'style.css').read_text(encoding='utf-8'))
    deck_id = 1_000_000_000 + int(hashlib.sha256(args.slug.encode()).hexdigest()[:7], 16)
    deck = genanki.Deck(deck_id, args.deck)
    for record in records:
        deck.add_note(genanki.Note(model=model, fields=[record[f] for f in FIELDS],
            guid=genanki.guid_for(record['ID']), tags=['anime_to_anki_example', args.slug]))
    package = genanki.Package(deck)
    package.media_files = [str(media/name) for name in sorted(hashes)]
    package.write_to_file(str(args.output/'cards.apkg'))
    with (args.output/'cards.tsv').open('w',encoding='utf-8',newline='') as stream:
        stream.write('#separator:Tab\n#html:true\n#notetype:subs2srs+\n#deck:'+args.deck+'\n')
        stream.write('#columns:'+'\t'.join(FIELDS)+'\n')
        writer = csv.writer(stream, delimiter='\t',lineterminator='\n')
        writer.writerows([[record[f] for f in FIELDS] for record in records])
    (args.output/'cards.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (args.output/'checksums.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'notes':len(records),'media':len(hashes),'output':str(args.output)},ensure_ascii=False))


if __name__ == '__main__':
    main()
