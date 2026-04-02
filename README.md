# Claude 技能集合 (Claude Skills Collection)

这是一套为 Claude AI 助手设计的技能集合，可以提升 Claude 在特定任务上的表现。

## 📚 目录

- [什么是技能？](#什么是技能)
- [包含的技能](#包含的技能)
- [如何使用](#如何使用)
- [安装方法](#安装方法)

## 🤔 什么是技能？

技能 (Skills) 是包含指令、脚本和资源的文件夹，Claude 可以动态加载这些技能来提升在特定任务上的表现。技能可以教 Claude 如何完成特定任务，比如：
- 使用公司品牌指南创建文档
- 按照特定工作流程分析数据
- 自动化个人任务

## 📂 包含的技能

本仓库包含以下技能模块：

### 🎨 创意与设计
- **algorithmic-art** - 算法艺术生成
- **canvas-design** - Canvas 设计工具
- **frontend-design** - 前端设计辅助

### 📄 文档处理
- **docx** - Word 文档创建与编辑
- **pdf** - PDF 文档处理
- **pptx** - PowerPoint 演示文稿生成
- **xlsx** - Excel 表格处理

### 🛠️ 开发与技术
- **mcp-builder** - MCP 服务器生成器
- **webapp-testing** - Web 应用测试
- **web-artifacts-builder** - Web 构件构建器

### 🏢 企业与沟通
- **brand-guidelines** - 品牌指南管理
- **de-ai-writing** - 去 AI 味儿写作与改稿
- **doc-coauthoring** - 文档协作
- **internal-comms** - 内部沟通
- **slack-gif-creator** - Slack GIF 创建器

### 🌟 特色技能
- **bilibili-subtitle** - B站视频字幕提取工具 ⭐
  - 支持关键词搜索视频
  - 按播放量/收藏/点赞排序
  - 批量提取字幕
  - 导出 JSON/TXT/SRT/Markdown 格式

- **skill-creator** - 技能创建器
- **theme-factory** - 主题工厂

## 🚀 如何使用

### 在 Claude Code 中使用

1. 安装 Claude Code
2. 将此仓库添加为插件市场：
```bash
/plugin marketplace add <你的用户名>/skills
```

3. 安装特定技能集：
```
- 打开 "浏览和安装插件"
- 选择对应的技能包
- 点击 "立即安装"
```

### 在 Claude.ai 中使用

付费用户可以直接在 Claude.ai 中使用这些技能。详细步骤请参考 [Claude 技能使用指南](https://support.claude.com/en/articles/12512180-using-skills-in-claude)。

### 通过 API 使用

可以通过 Claude API 使用这些技能。详情请查看 [Skills API 指南](https://docs.claude.com/en/api/skills-guide)。

## 📦 安装方法

### 方式1：直接下载

1. 点击页面右上角的 "Code" 按钮
2. 选择 "Download ZIP"
3. 解压到本地目录
4. 在 Claude 中导入该目录

### 方式2：Git 克隆

```bash
git clone https://github.com/<你的用户名>/skills.git
cd skills
```

### 方式3：作为插件安装

在 Claude Code 中直接安装：
```bash
/plugin install <技能名>@<你的用户名>-skills
```

## 📖 创建自定义技能

每个技能都是一个包含 `SKILL.md` 文件的文件夹。基本结构：

```markdown
---
name: my-skill-name
description: 技能的简短描述
---

# 我的技能名

[这里是 Claude 会遵循的指令]

## 使用示例
- 示例1
- 示例2

## 注意事项
- 注意事项1
- 注意事项2
```

## ⚠️ 免责声明

**这些技能仅供演示和教育目的。** 虽然某些功能可能在 Claude 中可用，但实际实现和行为可能与示例中显示的不同。这些技能旨在展示可能性和模式。在依赖关键任务之前，请务必在自己的环境中充分测试。

## 📄 许可证

部分技能采用 Apache 2.0 许可证开源。文档处理技能（docx、pdf、pptt、xlsx）采用源可用许可证。

详细信息请查看各技能目录中的许可证文件。

## 🔗 相关资源

- [Claude 技能官方文档](https://support.claude.com/en/articles/12512176-what-are-skills)
- [如何创建自定义技能](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [Agent Skills 规范](http://agentskills.io)
- [Anthropic 工程博客：Agent Skills](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

## 🤝 贡献

欢迎提交问题报告和改进建议！

## 📞 支持

如有问题，请：
1. 查看 [Claude 支持文档](https://support.claude.com)
2. 在 GitHub 上提交 Issue
3. 访问 [Claude 论坛](https://support.claude.com)

---

**享受使用 Claude 技能！** 🎉
