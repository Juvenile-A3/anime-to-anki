# 示例卡片

| 目录 | 内容 | 数量 |
| --- | --- | ---: |
| [yuruyuri](yuruyuri/) | 《ゆりゆららららゆるゆり大事件》音频卡，含封面、歌词、译文 | 51 |
| [rezero](rezero/) | Re:Zero 日中字幕与 WebM 片段 | 8 |

每个目录包含：

- `cards.apkg`：直接用 Anki 导入，已打包模板和全部媒体。
- `cards.tsv`：完整 15 字段，手动导入到 `subs2srs+` 时使用；需先安装模板和复制 `media/` 内文件到 `collection.media`。
- `cards.json`：可读的字段内容。
- `media/` 与 `checksums.json`：媒体及 SHA-256 校验和。

两种导入方式任选一种。示例使用新的 ID，不带个人复习进度、原笔记 ID、私人备注或本机路径。来源信息保留在歌曲字段和 Source 中。素材权利及来源见 [NOTICE.md](../NOTICE.md)。

## 导出自己的示例

打开 Anki 和 AnkiConnect，安装可选依赖：

```powershell
python -m pip install genanki
python tools/export_examples.py --query "deck:Japanese::Anime" --limit 8 --slug my-anime --deck "Examples::Anime" --output exports/my-anime
```

命令从仓库根目录运行。只支持 `subs2srs+` 笔记；使用 AnkiConnect 只读操作获取字段和媒体，然后用 genanki 生成新包。`--limit` 省略时导出所有匹配项。脚本不导出 Notes、Definition、Morph、Audio_Extra、原标签或学习记录；检测到公开字段含本机路径时会停止。分享前仍应检查实际内容。

输出目录必须是新的目录。需要更新已发布示例时，先在新目录中导出并检查，再替换目标文件。
