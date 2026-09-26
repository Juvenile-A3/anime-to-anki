"""Copy verified exported media into the open Anki profile via AnkiConnect.

Run without arguments for a read-only check; --install copies media only.
It does not import notes, change templates, decks or scheduling.
"""
import argparse
import base64
import csv
import hashlib
import json
from pathlib import Path
import urllib.request


def ac(action, **params):
    request = urllib.request.Request('http://127.0.0.1:8765',
        json.dumps(dict(action=action, version=6, params=params)).encode('utf-8'),
        {'Content-Type': 'application/json'})
    response = json.load(urllib.request.urlopen(request, timeout=90))
    if response['error']:
        raise RuntimeError(response['error'])
    return response['result']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    checks = json.loads((base/'checksums.json').read_text(encoding='utf-8'))
    for name, expected in checks.items():
        if Path(name).name != name:
            raise ValueError('Unsafe media name')
        if hashlib.sha256((base/'media'/name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Media checksum mismatch: {name}')
    print(f'{len(checks)} media files verified. AnkiConnect version: {ac("version")}')
    if not args.install:
        print('Read-only check complete. Use --install to copy media, then import music_import.tsv in Anki.')
        return
    for index, (name, expected) in enumerate(checks.items(), 1):
        existing = ac('retrieveMediaFile', filename=name)
        if existing:
            if hashlib.sha256(base64.b64decode(existing)).hexdigest() != expected:
                raise ValueError(f'Anki already contains different media named {name}; stopping without overwrite')
        else:
            returned = ac('storeMediaFile', filename=name, data=base64.b64encode((base/'media'/name).read_bytes()).decode('ascii'))
            if returned != name:
                raise ValueError(f'Unexpected media filename returned: {returned}')
        if index % 100 == 0: print(f'{index}/{len(checks)}', flush=True)
    print('Media ready. Import music_import.tsv in Anki; the existing subs2srs+ model shows covers and source information.')


if __name__ == '__main__':
    main()
