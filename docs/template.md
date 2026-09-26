# 统一 Anki 模板

维护目录：`model/subs2srs-plus/`。`front.html`、`back.html` 和 `style.css` 分别对应卡片正面、背面和样式。

通过 `anime-to-anki install-model` 安装为 `subs2srs+`，默认卡片名为 `Card 1`。也可在 Anki 卡片编辑器中手动复制，并按以下顺序创建字段：

```text
ID, Reading, Audio_Sentence, Screenshot, Expression, Chinese, Video,
Audio_Extra, Notes, Definition, Morph, Artist, SongTitle, Album, Source
```

| 字段 | 用途 |
| --- | --- |
| ID | 唯一标识，避免把同一句的不同媒体误认为相同笔记 |
| Expression / Reading | 日文原句 / Anki 注音格式；Reading 为空时显示 Expression |
| Chinese | 中文翻译 |
| Audio_Sentence / Audio_Extra | `[sound:文件名.mp3]` 音频引用 |
| Screenshot | 图片 HTML；有 Video 时隐藏图片 |
| Video | 带 src 的 video HTML |
| Morph / Definition | 重点词和释义 |
| Artist / SongTitle / Album / Source | 歌手、歌名、专辑与其他来源信息 |
| Notes | 只保存资料，不显示在卡面 |

正面以听音频/看视频为主，背面显示文本。视频默认最多连续播放 15 次；音频通过重复引用提供 5 次播放，实际自动播放取决于 Anki 设置。布局包含窄屏适配，但仍需在具体手机客户端验证。

背面默认加载 ichi.moe 查询原句，Jisho 按钮查询重点词（未填则查询原句）；使用时会把相应文字发送到该站点，也可能受站点 iframe 限制影响。离线使用可在背面模板中移除 `s2-lookup-column` 和对应查词脚本。

发布版移除了未提供的 `_kanjax_with_koohii v2.js`、`_jquery.bpopup.min.js` 引用，并用普通 `Definition` 字段替代依赖附加组件的 `edit:Definition`。无需这些脚本也能完成核心音视频与文本展示。未更改你本机 Anki 中已安装的模板。

示例 `.apkg` 使用独立笔记类型 `Anime to Anki Examples`，便于试用而不覆盖现有 `subs2srs+`。

## 效果截图

- [音乐卡片正反面](screenshots/music-card-preview.png)
- [动画卡片正反面](screenshots/anime-card-preview.png)

截图基于已发布示例的真实字段、媒体和本目录的模板生成，不是 Anki 应用窗口实拍。两侧预览保持同一套模板样式；浏览器中模拟了 Anki 的音频播放按钮，暂停视频，并收起在线查词区域。

重新生成预览页：

```powershell
python tools/build_card_previews.py
```

页面位于 `output/playwright/card-previews/music.html` 和 `anime.html`。使用 1280 × 900 的浏览器视口截图即可；脚本需要 FFmpeg 来提取真实视频画面，预览不请求外部网站，也不会修改 Anki。
