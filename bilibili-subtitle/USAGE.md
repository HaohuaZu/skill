# 使用说明

## Skill 激活

当用户提及以下关键词时，Claude 会自动激活此 skill：

- "B站字幕"
- "B站视频字幕"
- "提取字幕"
- "bilibili subtitle"
- "视频字幕提取"

## 典型使用场景

### 场景1：提取单个视频的字幕

**用户请求示例：**
```
请帮我从这个B站视频提取字幕：BV1Hwi4BYEJz
```

**Claude 会：**
1. 使用 `scripts/extract_single.py` 脚本
2. 修改脚本中的 BVID 为用户提供的 BV 号
3. 运行脚本并生成所有格式的字幕文件
4. 告知用户字幕已提取完成

### 场景2：批量提取多个视频的字幕

**用户请求示例：**
```
批量提取这些B站视频的字幕：
- BV1Hwi4BYEJz
- BV1QbruBUExb
- BV1bqi9BWE7M
```

**Claude 会：**
1. 将 BV 号列表添加到 `video_list.txt`
2. 使用 `scripts/extract_batch.py` 脚本
3. 批量处理所有视频
4. 将结果保存到 `subtitles/` 目录

### 场景3：指定输出格式

**用户请求示例：**
```
将这个B站视频的字幕提取为Markdown格式：BV1Hwi4BYEJz
```

**Claude 会：**
1. 提取字幕
2. 特别说明已生成 Markdown 格式的文件
3. 提供 Markdown 文件的路径

## 工作流程

### 步骤1：确认视频信息
- 获取用户提供的 BV 号
- 验证 BV 号格式（应为 BV 开头）
- 确认视频是否存在字幕

### 步骤2：选择提取方式
- 单个视频 → `extract_single.py`
- 多个视频 → `extract_batch.py`

### 步骤3：执行提取
- 调用相应的 Python 脚本
- 监控执行过程
- 处理可能的错误

### 步骤4：返回结果
- 列出生成的文件
- 说明字幕内容摘要
- 提供文件路径

## 输出文件说明

### 文件位置
- 单视频提取：当前工作目录
- 批量提取：`subtitles/` 子目录

### 文件格式说明

| 格式 | 文件扩展名 | 用途 |
|------|-----------|------|
| JSON | .json | 结构化数据，包含完整时间戳和元信息 |
| TXT | .txt | 纯文本，易于阅读和快速查看 |
| SRT | .srt | 标准字幕格式，可用于视频播放器 |
| Markdown | .md | 便于文档编辑和展示 |

## 错误处理

### 常见错误及解决方案

**错误1：视频不存在**
```
✗ 获取视频信息失败: 404 Not Found
```
解决方案：检查 BV 号是否正确

**错误2：视频没有字幕**
```
✗ 该视频没有可用的字幕
```
解决方案：确认视频是否上传了字幕

**错误3：网络错误**
```
✗ 获取视频信息失败: Connection timeout
```
解决方案：检查网络连接，稍后重试

## 最佳实践建议

1. **先测试单个视频**：批量提取前，先测试单个视频
2. **检查输出文件**：提取后检查文件是否完整
3. **保留原始数据**：JSON 格式包含最完整的信息
4. **合理使用**：遵守 B 站使用条款，仅用于个人学习

## 示例对话

### 示例1：基本提取

**用户：**
```
帮我从B站视频 BV1Hwi4BYEJz 提取字幕
```

**Claude：**
```
我会帮你从这个B站视频提取字幕。让我使用字幕提取工具来处理这个请求。

[运行提取脚本...]

✓ 成功获取视频信息: [视频标题]
✓ 找到 2 个字幕轨道

正在提取字幕 1/2: 中文（中国）
  ✓ 提取了 150 条字幕

正在提取字幕 2/2: English
  ✓ 提取了 150 条字幕

字幕提取完成！已生成以下文件：
- bilibili_subtitle_BV1Hwi4BYEJz.json
- bilibili_subtitle_BV1Hwi4BYEJz.txt
- bilibili_subtitle_BV1Hwi4BYEJz.srt
- bilibili_subtitle_BV1Hwi4BYEJz.md

共提取 2 个字幕轨道：中文（中国）、English
```

### 示例2：批量提取

**用户：**
```
批量提取这些视频的字幕：
BV1Hwi4BYEJz
BV1QbruBUExb
```

**Claude：**
```
我会帮你批量提取这些视频的字幕。让我创建视频列表并运行批量提取脚本。

[运行批量提取脚本...]

B站视频字幕批量提取工具
================================================================================

共找到 2 个视频需要处理

[1/2] 处理视频: BV1Hwi4BYEJz
--------------------------------------------------------------------------------
  ✓ 成功获取视频信息: [视频标题1]
  ✓ 找到 2 个字幕轨道
  ✓ JSON: subtitles/bilibili_subtitle_BV1Hwi4BYEJz.json
  ✓ TXT: subtitles/bilibili_subtitle_BV1Hwi4BYEJz.txt
  ✓ SRT: subtitles/bilibili_subtitle_BV1Hwi4BYEJz.srt
  ✓ Markdown: subtitles/bilibili_subtitle_BV1Hwi4BYEJz.md

  等待2秒后处理下一个视频...

[2/2] 处理视频: BV1QbruBUExb
--------------------------------------------------------------------------------
  ✓ 成功获取视频信息: [视频标题2]
  ✓ 找到 1 个字幕轨道
  ✓ JSON: subtitles/bilibili_subtitle_BV1QbruBUExb.json
  ✓ TXT: subtitles/bilibili_subtitle_BV1QbruBUExb.txt
  ✓ SRT: subtitles/bilibili_subtitle_BV1QbruBUExb.srt
  ✓ Markdown: subtitles/bilibili_subtitle_BV1QbruBUExb.md

================================================================================
批量提取完成!
成功: 2 个
失败: 0 个
总计: 2 个

字幕文件保存在: subtitles/
```

## 进阶使用

### 自定义输出目录

修改脚本中的 `OUTPUT_DIR` 变量可以自定义输出目录：

```python
OUTPUT_DIR = "my_subtitles"  # 批量提取
```

### 调整延迟时间

修改批量提取脚本中的延迟时间：

```python
time.sleep(2)  # 改为其他秒数
```

### 过滤字幕轨道

如果只需要特定语言的字幕，可以在脚本中添加过滤逻辑。
