from __future__ import annotations

import json
import math
from typing import Any
from urllib import request as urllib_request

from ..commands import IntegrationConfigError, SkillError, find_first_mapping_list
from ..models import ContentRecord
from ..normalize import normalize_wechat_mp_item, should_keep_record


def _sort_key(record: ContentRecord, sort_by: str) -> int | str:
    if sort_by == "read":
        return record.read_count
    if sort_by == "like":
        return record.like_count
    if sort_by == "comment":
        return record.comment_count
    if sort_by == "publish_time":
        return record.publish_time
    return record.read_count + record.like_count + record.comment_count


class WechatMPAdapter:
    def __init__(self, api_url: str | None, api_key: str | None = None) -> None:
        self._api_url = api_url
        self._api_key = api_key

    def collect(self, keyword: str, days: int, top_n: int, sort_by: str, collect_date: str) -> list[ContentRecord]:
        if not self._api_url:
            raise IntegrationConfigError("wechat_mp collection requires CN8N_API_URL")
        first_page = self._fetch_page(keyword=keyword, days=days, page=1)
        page_size = max(int(first_page.get("data_number") or len(first_page.get("data", [])) or 20), 1)
        total_pages = int(first_page.get("total_page") or 1)
        requested_pages = calculate_fetch_pages(top_n=top_n, page_size=page_size, max_pages=total_pages)

        items: list[dict[str, Any]] = list(first_page.get("data", []))
        for page in range(2, requested_pages + 1):
            page_payload = self._fetch_page(keyword=keyword, days=days, page=page)
            items.extend(page_payload.get("data", []))

        records = [normalize_wechat_mp_item(keyword=keyword, raw_item=item, collect_date=collect_date) for item in items]
        filtered = [record for record in records if should_keep_record(record.publish_time, collect_date, days)]
        return sorted(filtered, key=lambda item: _sort_key(item, sort_by), reverse=True)[:top_n]

    def _fetch_page(self, keyword: str, days: int, page: int) -> dict[str, Any]:
        payload = build_cn8n_payload(keyword=keyword, days=days, page=page)
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        req = urllib_request.Request(
            self._api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))

        if body.get("code") != 0:
            raise SkillError(f"wechat_mp API failed: code={body.get('code')} msg={body.get('msg')}")

        data = body.get("data")
        if not isinstance(data, dict):
            raise SkillError("wechat_mp API returned invalid data payload")

        items = find_first_mapping_list(data, ("data", "items", "articles", "results"))
        return {
            "data": items,
            "data_number": int(data.get("data_number") or len(items) or 0),
            "total_page": int(data.get("total_page") or 1),
            "total": int(data.get("total") or len(items) or 0),
            "page": int(data.get("page") or page),
        }


def build_cn8n_payload(keyword: str, days: int, page: int) -> dict[str, Any]:
    return {
        "kw": keyword,
        "sort_type": 1,
        "mode": 1,
        "period": days,
        "page": page,
        "any_kw": "",
        "ex_kw": "",
        "verifycode": "",
        "type": 1,
    }


def calculate_fetch_pages(top_n: int, page_size: int, max_pages: int) -> int:
    if top_n <= 0:
        return 1
    if page_size <= 0:
        return 1
    return max(1, min(max_pages, math.ceil(top_n / page_size)))
