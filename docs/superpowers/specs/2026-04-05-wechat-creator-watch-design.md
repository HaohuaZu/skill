# 微信公众号博主监控设计

## 目标

在现有 `content-collection-topic-analysis-skill` 内新增一个“公众号博主监控”能力。该能力每天监控指定公众号账号的新文章，并将符合条件的文章写入现有飞书多维表格，作为长期内容资产的一部分。

本次只支持微信公众号，且只支持“精确公众号名匹配”。

## 监控对象

第一版固定支持以下公众号：

- `饼干哥哥 AGI`
- `数字生命卡兹克`
- `TATALAB`

后续监控名单不写死在代码里，而是通过配置文件加载。

## 设计原则

- 复用现有采集与写库链路，不新开第二套系统
- 将“关键词采集”和“博主监控”视为两种采集模式
- 监控模式的实现优先保持最小改动
- 写入仍然使用现有飞书内容表
- 幂等去重优先基于文章本身，而不是触发条件

## 方案选择

### 方案 A：复用现有内容表，新增监控模式字段

优点：

- 改动最小
- 现有飞书读取、筛选、复盘链路不需要拆分
- 与当前 Skill 的“统一内容资产”方向一致

缺点：

- 表内会混合关键词采集和博主监控数据

### 方案 B：新建独立监控表

优点：

- 数据边界更清晰

缺点：

- 需要维护第二张内容表
- 后续分析和汇总时要跨表

### 决策

采用方案 A。继续写入现有内容表，并新增监控相关字段来区分数据来源。

## 输入与运行方式

新增一条独立入口：

- `content-collection-topic-analysis-skill/scripts/run_creator_watch.py`

新增配置文件：

- `content-collection-topic-analysis-skill/config/creator_watchlist.json`

配置文件第一版结构：

```json
{
  "platform": "wechat_mp",
  "match_mode": "exact",
  "creators": [
    "饼干哥哥 AGI",
    "数字生命卡兹克",
    "TATALAB"
  ]
}
```

运行时支持：

- 手动触发：默认抓取最近 1 天
- 定时触发：后续通过 cron 或 automation 调用同一个入口

## 数据流

### 1. 读取监控名单

入口脚本读取 `creator_watchlist.json`，并构造监控请求对象。

### 2. 调用公众号搜索接口

对每个 `creator_name`，调用现有 cn8n 公众号搜索接口。调用方式仍沿用当前 `wechat_mp` adapter。

搜索词直接使用公众号名本身。

### 3. 二次过滤

对接口返回结果执行精确匹配：

- `wx_name == creator_name`

不接受模糊匹配、前缀匹配或包含匹配。

### 4. 时间范围过滤

只保留最近 `N` 天内的新文章，第一版默认 `1` 天。

### 5. 标准化

复用现有 `ContentRecord` 结构，并在写库字段映射中补充监控来源信息。

### 6. 去重

去重主键从“依赖 keyword”升级为优先依赖文章本身：

- `record_key = platform + "|" + url`

如果 `url` 缺失，再回退为：

- `platform + "|" + title + "|" + author + "|" + publish_time`

这样同一篇文章不会因为不同关键词任务或不同监控任务重复写入。

### 7. 写入飞书

继续写入现有内容表，缺字段时自动补齐。

## 内容表字段变更

在现有内容表字段基础上新增：

- `monitor_type`
- `creator_name`
- `match_author`

字段含义：

- `monitor_type`
  - `keyword`：关键词采集
  - `creator_watch`：博主监控
- `creator_name`
  - 本次监控配置中的目标公众号名
- `match_author`
  - 最终命中的 `wx_name`

对于关键词采集历史数据：

- `monitor_type` 写 `keyword`
- `creator_name` 留空
- `match_author` 可留空或写实际作者

对于博主监控数据：

- `monitor_type` 写 `creator_watch`
- `creator_name` 写配置中的公众号名
- `match_author` 写返回结果中的 `wx_name`

## 代码结构

### 新增文件

- `content-collection-topic-analysis-skill/config/creator_watchlist.json`
- `content-collection-topic-analysis-skill/scripts/run_creator_watch.py`

### 需修改文件

- `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/models.py`
  - 为 `ContentRecord` 增加监控来源字段
- `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/lark_base.py`
  - 补充字段定义和记录映射
- `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/pipeline.py`
  - 调整改进后的去重键逻辑
- `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/adapters/wechat_mp.py`
  - 补充基于 creator watch 的采集入口或共用方法
- `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/config.py`
  - 支持 creator watch 配置路径
- `content-collection-topic-analysis-skill/tests/test_pipeline_core.py`
  - 增加监控模式相关单测

### 可选新增文件

- `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/creator_watch.py`
  - 如果入口编排逻辑变多，则拆出独立模块

第一版不强制拆此文件，优先保持实现最小。

## 错误处理

- 配置文件不存在：启动失败并给出明确错误
- 配置文件为空：返回 0 条结果，不报错
- 某个公众号搜索失败：
  - 记录错误
  - 不阻塞其它公众号继续执行
- 飞书写入失败：
  - 返回失败并中止本次执行

## 测试策略

第一版必须覆盖：

1. 精确匹配逻辑
   - `wx_name` 完全相等才算命中
2. 时间范围过滤
   - 超出 1 天的文章被过滤
3. 去重键升级
   - 同一 URL 的文章不会重复写入
4. 飞书字段映射
   - `monitor_type`
   - `creator_name`
   - `match_author`
5. 入口编排
   - 监控名单中多个公众号可依次处理

## 暂不包含

- 小红书博主监控
- 监控结果自动触发选题分析
- 监控结果自动触发内容创作
- 自动创建独立监控表
- 自动定时任务创建

## 验收标准

- 能从配置文件读取指定公众号名单
- 能对每个公众号执行采集与精确匹配
- 能过滤出最近 1 天的新文章
- 能写入现有飞书内容表
- 内容表中能明确区分 `keyword` 与 `creator_watch`
- 重复执行不会产生同一篇文章的重复记录
