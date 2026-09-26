"""Build offline screenshot pages from the published templates and example cards.

Run from any directory with Python 3.11+ and ffmpeg on PATH. Open the resulting
output/playwright/card-previews/*.html pages at 1280 x 900, then take screenshots.
This renders template previews, not screenshots of the Anki application.
"""
import base64
import html
import json
import mimetypes
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output/playwright/card-previews'


def data_url(path):
    mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()


def render(template, fields):
    section = re.compile(r'{{([#^])(\w+)}}(.*?){{/\2}}', re.S)
    while section.search(template):
        template = section.sub(lambda m: m[3] if bool(fields.get(m[2])) == (m[1] == '#') else '', template)
    template = re.sub(r'{{(?:furigana:)?(\w+)}}', lambda m: fields.get(m[1], ''), template)
    # Avoid autoplay and external dictionary requests in an offline screenshot.
    template = re.sub(r'<script\b[^>]*>.*?</script>', '', template, flags=re.S)
    return template


def card_page(fields, side):
    model = ROOT / 'model/subs2srs-plus'
    body = render((model/f'{side}.html').read_text(encoding='utf-8'), fields)
    # Anki replaces [sound:...] with a replay button. Mimic its appearance here;
    # no audio is played and no Anki add-on or application state is required.
    replay = '<button class="preview-replay" aria-label="播放句子"><svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="29" fill="#4c535a"/><path d="M25 18 L46 32 L25 46Z" fill="#eff2f5"/></svg></button>'
    body = re.sub(r'\[sound:[^\]]+\]', replay, body)
    css = (model/'style.css').read_text(encoding='utf-8')
    css += '\n.preview-replay{border:0;background:none;padding:0;width:44px;height:44px}.preview-replay svg{width:44px;height:44px}'
    return '<!doctype html><meta charset="utf-8"><style>'+css+'</style><body class="card nightMode">'+body+'</body>'


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    items = [
        ('music', 'yuruyuri', 0, '音乐卡片', '摇曳百合 · ゆりゆららららゆるゆり大事件', '听句子音频', '查看日文与中文释义'),
        ('anime', 'rezero', 2, '动画卡片', 'Re:Zero · 字幕与视频片段', '观看原声片段', '结合上下文理解台词'),
    ]
    for name, slug, index, title, subtitle, front_label, back_label in items:
        folder = ROOT/'examples'/slug
        fields = json.loads((folder/'cards.json').read_text(encoding='utf-8'))[index]
        fields = dict(fields)
        if fields['Screenshot']:
            filename = re.search(r'src="([^"]+)"', fields['Screenshot'])[1]
            fields['Screenshot'] = fields['Screenshot'].replace(filename, data_url(folder/'media'/filename))
        if fields['Video']:
            filename = re.search(r'src="([^"]+)"', fields['Video'])[1]
            poster = OUTPUT / f'{name}-frame.png'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '0.65', '-i', str(folder/'media'/filename),
                            '-frames:v', '1', str(poster)], check=True, capture_output=True)
            fields['Video'] = re.sub(r'<video\b', '<video poster="'+data_url(poster)+'"', fields['Video'])
            fields['Video'] = fields['Video'].replace(filename, data_url(folder/'media'/filename))
        panes = []
        for side, label, caption in [('front', '正面', front_label), ('back', '背面', back_label)]:
            frame = html.escape(card_page(fields, side), quote=True)
            panes.append(f'<section class="pane"><div class="pane-label"><b>{label}</b><span>{caption}</span></div><iframe title="{title}{label}" srcdoc="{frame}"></iframe></section>')
        page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>'''+title+''' · Anime to Anki</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#10171b;color:#e9f0f4;font-family:"Segoe UI","Microsoft YaHei",sans-serif}
.sheet{width:1280px;padding:38px 46px 26px}.eyebrow{font-size:13px;font-weight:600;letter-spacing:2px;color:#79cbb7}
header{display:flex;align-items:flex-end;justify-content:space-between;margin:14px 0 27px}h1{font-size:34px;line-height:1.2;margin:0 0 10px;font-weight:650}
.subtitle{margin:0;color:#aebdc7;font-size:16px}.badge{border:1px solid #35444c;border-radius:20px;color:#b5d9cc;font-size:13px;padding:8px 16px}
.panes{display:grid;grid-template-columns:1fr 1fr;gap:22px}.pane{border:1px solid #344148;border-radius:14px;overflow:hidden;background:#161819}
.pane-label{height:55px;display:flex;align-items:center;gap:15px;padding:0 20px;background:#202a30;border-bottom:1px solid #344148}
.pane-label b{font-size:17px;font-weight:600}.pane-label span{color:#aab9c1;font-size:13px}iframe{display:block;width:100%;height:610px;border:0}
footer{display:flex;justify-content:space-between;align-items:center;margin-top:19px;font-size:12px;color:#83969f;line-height:1.6}
</style><main class="sheet"><div class="eyebrow">ANIME TO ANKI / CARD PREVIEW</div><header><div><h1>'''+title+'''</h1><p class="subtitle">'''+subtitle+'''</p></div><div class="badge">subs2srs+ · 统一模板</div></header><div class="panes">'''+''.join(panes)+'''</div><footer><span>仓库真实模板与示例媒体的浏览器预览 · 播放按钮作展示 · 在线查词已收起</span><span>github.com/Juvenile-A3/anime-to-anki</span></footer></main></html>'''
        target = OUTPUT / f'{name}.html'
        target.write_text(page, encoding='utf-8')
        print(target)


if __name__ == '__main__':
    main()
