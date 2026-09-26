# 音乐制卡

`tools/music/music_to_anki.py` 由个人音乐卡片修复脚本整理而来，使用 Python 标准库和系统 FFmpeg / ffprobe。

## 单曲和批量

```powershell
python tools/music/music_to_anki.py --audio song.mp3 --japanese ja.srt --chinese zh.srt --output exports/song --deck "Japanese::Music"
```

中文字幕可省略，音频可以是 FFmpeg 支持的本地格式。日文与中文字幕都需使用 UTF-8 SRT。

批量清单 `songs.json`：

```json
[
  {"audio": "music/song1.mp3", "japanese": "lyrics/song1.ja.srt", "chinese": "lyrics/song1.zh.srt"},
  {"audio": "music/song2.flac", "japanese": "lyrics/song2.ja.srt"}
]
```

相对路径以清单所在目录为基准：

```powershell
python tools/music/music_to_anki.py --manifest songs.json --output exports/batch --workers 4 --deck "Japanese::Music"
```

## 处理与复核

每句前后保留 250 ms，输出 192 kbps、44.1 kHz、双声道 MP3。歌曲信息来自音频元数据，存在内嵌封面时提取封面。不会自动联网搜索歌词或生成注音。

优先匹配完全相同的中日字幕时间范围；否则使用覆盖比例足够的重叠字幕，并将其列入复核表。作者信息等字幕会按规则跳过。长于 15 秒的片段另外列出，便于排除间奏、尾奏或错误时间轴。

- `music_import.tsv`：完整字段及目标牌组。
- `media/`：句子音频与封面。
- `validation.json`、`checksums.json`：解码时长验证和 SHA-256。
- `需要复核的翻译.tsv`、`需要复核的长切片.tsv`：人工检查列表。
- `preparation_errors.json`：无法处理的输入。存在错误时保留成功部分，并以非零状态退出。
- `manifest.json`：来源路径和详细切片信息，用于本地诊断，分享前应移除个人路径。

用输出目录内的 `install_media.py --install` 复制媒体，再在 Anki 中导入 TSV；脚本本身不添加笔记。对已有文件会检查冲突。调整输入、时间轴或编码参数时使用新的输出目录，避免复用之前已生成的片段。

歌词时间轴和译文匹配仍需人工核对；通过解码检查只说明媒体可解码、时长符合要求。
