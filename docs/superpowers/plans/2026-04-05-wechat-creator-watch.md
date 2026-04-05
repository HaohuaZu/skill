# WeChat Creator Watch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a WeChat creator-watch mode that monitors exact公众号 names daily and writes matched articles into the existing Lark content table.

**Architecture:** Reuse the existing `wechat_mp` collection path, but introduce a creator-watch entrypoint and config loader. Persist the same `ContentRecord` structure with extra monitor metadata, and upgrade deduplication to prefer article identity over trigger keyword.

**Tech Stack:** Python 3, dataclasses, existing cn8n WeChat API adapter, existing Lark CLI writer, unittest

---

### Task 1: Add the creator-watch plan inputs and config loader

**Files:**
- Create: `content-collection-topic-analysis-skill/config/creator_watchlist.json`
- Create: `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/creator_watch.py`
- Modify: `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/config.py`
- Test: `content-collection-topic-analysis-skill/tests/test_pipeline_core.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_skill_config_reads_creator_watchlist_override(self) -> None:
    from content_collection_topic_analysis.config import SkillConfig

    with patch.dict("os.environ", {"CREATOR_WATCHLIST_PATH": "/tmp/watch.json"}, clear=False):
        config = SkillConfig.from_env()

    self.assertEqual(config.creator_watchlist_path, "/tmp/watch.json")


def test_load_creator_watchlist_reads_exact_creators(self) -> None:
    from content_collection_topic_analysis.creator_watch import load_creator_watchlist

    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "watch.json"
        path.write_text(
            json.dumps(
                {
                    "platform": "wechat_mp",
                    "match_mode": "exact",
                    "creators": ["饼干哥哥 AGI", "数字生命卡兹克", "TATALAB"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        watch = load_creator_watchlist(str(path))

    self.assertEqual(watch.platform, "wechat_mp")
    self.assertEqual(watch.match_mode, "exact")
    self.assertEqual(watch.creators, ["饼干哥哥 AGI", "数字生命卡兹克", "TATALAB"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest content-collection-topic-analysis-skill.tests.test_pipeline_core -v`
Expected: FAIL with missing `creator_watchlist_path` and missing `creator_watch` module helpers.

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class CreatorWatchConfig:
    platform: str
    match_mode: str
    creators: list[str]


def load_creator_watchlist(path: str) -> CreatorWatchConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return CreatorWatchConfig(
        platform=str(payload.get("platform") or "wechat_mp"),
        match_mode=str(payload.get("match_mode") or "exact"),
        creators=[str(item).strip() for item in payload.get("creators", []) if str(item).strip()],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest content-collection-topic-analysis-skill.tests.test_pipeline_core -v`
Expected: PASS for the new config-loader tests.

- [ ] **Step 5: Commit**

```bash
git add content-collection-topic-analysis-skill/config/creator_watchlist.json \
  content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/creator_watch.py \
  content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/config.py \
  content-collection-topic-analysis-skill/tests/test_pipeline_core.py
git commit -m "feat: add creator watch config loading"
```

### Task 2: Extend content records and Lark mapping for creator-watch

**Files:**
- Modify: `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/models.py`
- Modify: `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/lark_base.py`
- Test: `content-collection-topic-analysis-skill/tests/test_pipeline_core.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_content_field_specs_include_creator_watch_fields(self) -> None:
    from content_collection_topic_analysis.lark_base import CONTENT_FIELD_SPECS

    spec_by_name = {item["name"]: item for item in CONTENT_FIELD_SPECS}
    self.assertEqual(spec_by_name["monitor_type"]["type"], "select")
    self.assertEqual(spec_by_name["creator_name"]["type"], "text")
    self.assertEqual(spec_by_name["match_author"]["type"], "text")


def test_content_payload_includes_creator_watch_fields(self) -> None:
    from content_collection_topic_analysis.lark_base import LarkBaseWriter
    from content_collection_topic_analysis.models import ContentRecord

    payload = LarkBaseWriter._content_payload(
        ContentRecord(
            platform="wechat_mp",
            keyword="数字生命卡兹克",
            title="示例",
            summary="摘要",
            author="数字生命卡兹克",
            publish_time="2026-04-05T09:00:00",
            url="https://example.com/a",
            read_count=1,
            like_count=2,
            comment_count=3,
            raw_content="正文",
            collect_date="2026-04-05",
            monitor_type="creator_watch",
            creator_name="数字生命卡兹克",
            match_author="数字生命卡兹克",
        )
    )

    self.assertEqual(payload["monitor_type"], "creator_watch")
    self.assertEqual(payload["creator_name"], "数字生命卡兹克")
    self.assertEqual(payload["match_author"], "数字生命卡兹克")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest content-collection-topic-analysis-skill.tests.test_pipeline_core -v`
Expected: FAIL because the fields and payload keys do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class ContentRecord:
    ...
    monitor_type: str = "keyword"
    creator_name: str = ""
    match_author: str = ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest content-collection-topic-analysis-skill.tests.test_pipeline_core -v`
Expected: PASS for field and payload tests.

- [ ] **Step 5: Commit**

```bash
git add content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/models.py \
  content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/lark_base.py \
  content-collection-topic-analysis-skill/tests/test_pipeline_core.py
git commit -m "feat: add creator watch content fields"
```

### Task 3: Upgrade deduplication to prefer article identity

**Files:**
- Modify: `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/models.py`
- Test: `content-collection-topic-analysis-skill/tests/test_pipeline_core.py`

- [ ] **Step 1: Write the failing test**

```python
def test_deduplicate_records_ignores_keyword_when_url_matches(self) -> None:
    from content_collection_topic_analysis.models import ContentRecord
    from content_collection_topic_analysis.pipeline import deduplicate_records

    first = ContentRecord(
        platform="wechat_mp",
        keyword="A",
        title="同一篇文章",
        summary="",
        author="数字生命卡兹克",
        publish_time="2026-04-05T09:00:00+08:00",
        url="https://example.com/1",
        read_count=0,
        like_count=10,
        comment_count=1,
        raw_content="",
        collect_date="2026-04-05",
    )
    duplicate = replace(first, keyword="B", like_count=999)

    records = deduplicate_records([first, duplicate])
    self.assertEqual(len(records), 1)
    self.assertEqual(records[0].keyword, "A")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest content-collection-topic-analysis-skill.tests.test_pipeline_core.PipelineCoreTests.test_deduplicate_records_ignores_keyword_when_url_matches -v`
Expected: FAIL because the current record key includes `keyword`.

- [ ] **Step 3: Write minimal implementation**

```python
@property
def record_key(self) -> str:
    if self.url:
        return _stable_hash([self.platform, self.url])
    return _stable_hash([self.platform, self.title, self.author, self.publish_time])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest content-collection-topic-analysis-skill.tests.test_pipeline_core.PipelineCoreTests.test_deduplicate_records_ignores_keyword_when_url_matches -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/models.py \
  content-collection-topic-analysis-skill/tests/test_pipeline_core.py
git commit -m "feat: dedupe records by article identity"
```

### Task 4: Add exact-author matching in the WeChat adapter

**Files:**
- Modify: `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/adapters/wechat_mp.py`
- Test: `content-collection-topic-analysis-skill/tests/test_pipeline_core.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_filter_records_by_exact_author(self) -> None:
    from content_collection_topic_analysis.adapters.wechat_mp import filter_records_by_exact_author
    from content_collection_topic_analysis.models import ContentRecord

    records = [
        ContentRecord(..., author="数字生命卡兹克", url="https://example.com/1", collect_date="2026-04-05"),
        ContentRecord(..., author="数字生命卡兹克 Pro", url="https://example.com/2", collect_date="2026-04-05"),
    ]

    filtered = filter_records_by_exact_author(records, "数字生命卡兹克")

    self.assertEqual([item.author for item in filtered], ["数字生命卡兹克"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest content-collection-topic-analysis-skill.tests.test_pipeline_core -v`
Expected: FAIL because the helper does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
def filter_records_by_exact_author(records: list[ContentRecord], author_name: str) -> list[ContentRecord]:
    return [record for record in records if record.author == author_name]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest content-collection-topic-analysis-skill.tests.test_pipeline_core -v`
Expected: PASS for the new helper.

- [ ] **Step 5: Commit**

```bash
git add content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/adapters/wechat_mp.py \
  content-collection-topic-analysis-skill/tests/test_pipeline_core.py
git commit -m "feat: support exact author filtering for wechat"
```

### Task 5: Add the creator-watch entrypoint and runner

**Files:**
- Create: `content-collection-topic-analysis-skill/scripts/run_creator_watch.py`
- Modify: `content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/creator_watch.py`
- Test: `content-collection-topic-analysis-skill/tests/test_pipeline_core.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_help_lists_creator_watch_flags(self) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_creator_watch.py"), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn("--days", result.stdout)
    self.assertIn("--top-n", result.stdout)
    self.assertIn("--watchlist", result.stdout)


def test_creator_watch_runner_collects_multiple_creators(self) -> None:
    from content_collection_topic_analysis.creator_watch import run_creator_watch
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest content-collection-topic-analysis-skill.tests.test_pipeline_core -v`
Expected: FAIL because the script and runner do not exist.

- [ ] **Step 3: Write minimal implementation**

```python
def run_creator_watch(...):
    records = []
    for creator in watch.creators:
        matched = filter_records_by_exact_author(
            adapter.collect(keyword=creator, days=days, top_n=top_n, sort_by="publish_time", collect_date=collect_date),
            creator,
        )
        records.extend(
            replace(record, keyword=creator, monitor_type="creator_watch", creator_name=creator, match_author=record.author)
            for record in matched
        )
    unique = deduplicate_records(records)
    writer.write_content_records(unique)
    return unique
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest content-collection-topic-analysis-skill.tests.test_pipeline_core -v`
Expected: PASS for the new entrypoint tests.

- [ ] **Step 5: Commit**

```bash
git add content-collection-topic-analysis-skill/scripts/run_creator_watch.py \
  content-collection-topic-analysis-skill/scripts/content_collection_topic_analysis/creator_watch.py \
  content-collection-topic-analysis-skill/tests/test_pipeline_core.py
git commit -m "feat: add wechat creator watch entrypoint"
```

### Task 6: Run full verification

**Files:**
- Verify only

- [ ] **Step 1: Run focused tests**

Run: `python3 -m unittest content-collection-topic-analysis-skill.tests.test_pipeline_core -v`
Expected: PASS

- [ ] **Step 2: Run full suite**

Run: `python3 -m unittest discover -s content-collection-topic-analysis-skill/tests -v`
Expected: PASS

- [ ] **Step 3: Commit final polish if needed**

```bash
git add content-collection-topic-analysis-skill
git commit -m "test: verify creator watch integration"
```
