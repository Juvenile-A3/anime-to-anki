# 安装、配置与快捷键

## 依赖

- [Python](https://www.python.org/downloads/) 3.11+
- [mpv](https://mpv.io/installation/)
- [FFmpeg](https://ffmpeg.org/download.html)，音乐工具还使用同包中的 ffprobe
- [Anki](https://apps.ankiweb.net/) 与 [AnkiConnect](https://ankiweb.net/shared/info/2055492159)（直接制卡、模板安装和媒体复制时需要）

在克隆目录运行 `python -m pip install -e .`。确保 mpv 使用的 Python 与安装命令是同一解释器。

## 配置位置

优先级：命令行 `--config` → 环境变量 `ANIME_TO_ANKI_CONFIG` → 当前目录 `config.toml` → 默认配置路径。

- Windows：`%APPDATA%\anime-to-anki\config.toml`
- 其他平台：`~/.config/anime-to-anki/config.toml`

新建目录后复制 `examples/config.toml`，将 `[anki] enabled = true`。打开 Anki 并创建配置中指定的牌组。`install-model` 会创建 `subs2srs+`；若已有同名类型，会更新其模板和样式，因此修改前建议自行导出备份。

```powershell
anime-to-anki install-model
anime-to-anki doctor
```

现有同名类型缺少必需字段时会报错，不会自动迁移已有笔记。

## mpv 主脚本

把 `mpv/anime-to-anki.lua` 放到 mpv 配置目录的 `scripts/`。可在 `script-opts/anime_to_anki.conf` 中写：

```ini
python=python
key=Ctrl+a
# config 可省略以使用默认配置位置
```

未配置时快捷键为 `a`。如果 Python 不在 PATH，`python=` 使用安装该项目的解释器路径。重启 mpv 后生效。

字幕配置：

- 双字幕轨默认主轨日语、第二轨中文；反过来时设置 `[text] primary_subtitle_language = "chinese"`。
- 单轨双语字幕自动按行和语言特征拆分；也可以使用 `split_mode = "first_chinese"` 或 `"first_japanese"`。
- 可读取外部或同目录 ASS 字幕的样式和时间轴；无法识别时使用 mpv 提供的字幕文字。

## 手动导入动画 TSV

动画导出的四列依次是 `Japanese`、`Chinese`、`Clip`、`Source`，不带 ID。可以创建对应四字段笔记类型，正面写 `{{Japanese}}<br>{{Clip}}`，背面写 `{{FrontSide}}<hr>{{Chinese}}<br>{{Source}}`，导入时启用 HTML。

媒体需要单独复制到当前 Anki 用户的 `collection.media`。若希望使用统一 `subs2srs+` 类型，推荐启用 AnkiConnect 自动填入 ID 和对应字段；音乐及仓库示例 TSV 已包含完整的 15 字段。

## 可选 mpv 脚本

按需复制以下文件，不需要全部安装：

| 文件 | 功能与影响 |
| --- | --- |
| `anime-seek.lua` | 强制绑定左右方向键，精确前后跳转 5 秒 |
| `anime-subtitle-defaults.lua` | 加载媒体时根据轨道标签选择日中字幕 |
| `anime-screenshot.lua` + `anime-screenshot-copy.ps1` | Windows 下绑定 `s`，保存带字幕截图并复制到剪贴板；保存到 mpv 截图目录，未设置则使用工作目录 |
| `bilingual-lrc.lua` | 将相同时间戳的多行 LRC 在内存中合并，避免双语歌词只显示一行；原文件不变 |

LRC 辅助脚本用于 mpv 显示；音乐批量制卡入口读取 SRT。UTF-16 和增强型逐字歌词需先转换成工具支持的格式。

## 常见问题

- `doctor` 找不到 FFmpeg：把 FFmpeg 加到 PATH，或为动画工具配置 `ffmpeg_path`。音乐工具需要 PATH 中同时存在 ffmpeg / ffprobe。
- mpv 提示无法导入模块：检查 `python=` 是否指向正确解释器。
- AnkiConnect 连接失败：打开 Anki，检查插件是否安装，并确认服务位于 `http://127.0.0.1:8765`。
- 视频无法自动播放：点击播放按钮；不同 Anki 客户端可能有不同的自动播放或编码支持。
- 翻译错位：先核对原曲/视频版本与字幕时间轴，再调整字幕或切片参数。
