# B站视频字幕提取工具

这是一个用于从B站（Bilibili）视频中提取字幕的工具，支持单个视频提取和批量处理。

## 功能特性

- ✅ 支持单个视频字幕提取
- ✅ 支持批量视频字幕提取
- ✅ 多格式导出：JSON、TXT、SRT、Markdown
- ✅ 自动处理编码问题
- ✅ 完善的错误处理

## 快速开始

### 环境要求

- Python 3.6+
- requests 库

### 安装依赖

```bash
pip install requests
```

### 单个视频提取

1. 编辑 `scripts/extract_single.py` 文件
2. 修改 `BVID` 变量为目标视频的BV号
3. 运行脚本：

```bash
python scripts/extract_single.py
```

### 批量视频提取

1. 编辑 `scripts/video_list.txt` 文件
2. 添加视频BV号（每行一个）
3. 运行批量提取脚本：

```bash
python scripts/extract_batch.py
```

## 输出格式

脚本会生成以下格式的字幕文件：

- **JSON** - 结构化数据，包含完整时间戳和元信息
- **TXT** - 纯文本格式，适合快速查看
- **SRT** - 标准字幕格式，可用于视频播放器
- **Markdown** - 便于文档编辑和查看

## 使用示例

### 视频列表文件格式

在 `video_list.txt` 中添加视频BV号：

```
# 这是注释行
BV1Hwi4BYEJz
BV1QbruBUExb
BV1bqi9BWE7M
```

### 输出文件命名

生成的文件名格式为：`bilibili_subtitle_{BV号}.{格式}`

例如：
- `bilibili_subtitle_BV1Hwi4BYEJz.json`
- `bilibili_subtitle_BV1Hwi4BYEJz.txt`
- `bilibili_subtitle_BV1Hwi4BYEJz.srt`
- `bilibili_subtitle_BV1Hwi4BYEJz.md`

## 注意事项

1. 确保网络连接正常
2. 部分视频可能没有字幕
3. 批量提取时会自动添加延迟，避免请求过于频繁
4. 仅用于个人学习和研究，请遵守B站使用条款

## 故障排除

### 无法获取视频信息
- 检查网络连接
- 确认BV号是否正确
- 检查视频是否存在

### 编码问题
- 脚本已自动处理UTF-8编码
- 确保终端支持UTF-8显示

## 技术实现

- 使用B站公开API获取视频信息和字幕
- 支持多字幕轨道提取
- 自动时间戳格式转换
- 完善的异常处理机制

## 许可证

Apache License 2.0

## 贡献

欢迎提交问题和改进建议！
