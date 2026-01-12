#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查B站视频字幕情况
"""

import json
import sys
import io
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def load_cookies():
    """加载cookies"""
    with open("cookies_template.json", 'r', encoding='utf-8') as f:
        return json.load(f)


def check_subtitle_types(bvid: str, cookies: dict):
    """检查不同类型的字幕"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com',
        'Accept': 'application/json',
    }

    # 获取视频信息
    info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    response = requests.get(info_url, headers=headers, cookies=cookies, timeout=10)
    data = response.json()

    if data.get('code') != 0:
        print(f"✗ API错误: {data.get('message')}")
        return

    video_data = data.get('data', {})
    title = video_data.get('title', '未知标题')
    cid = video_data.get('cid', 0)

    print(f"✓ 视频标题: {title}")
    print(f"  CID: {cid}\n")

    # 检查播放器API (AI字幕)
    print("=" * 80)
    print("检查播放器API (AI字幕):")
    print("=" * 80)

    player_url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
    response = requests.get(player_url, headers=headers, cookies=cookies, timeout=10)
    player_data = response.json()

    subtitle_info = player_data.get('data', {}).get('subtitle', {})
    subtitles_list = subtitle_info.get('subtitles', [])

    print(f"找到 {len(subtitles_list)} 个字幕轨道:")

    for idx, sub in enumerate(subtitles_list):
        print(f"\n字幕 {idx + 1}:")
        print(f"  语言: {sub.get('lan_doc', '未知')}")
        print(f"  语言代码: {sub.get('lan', '')}")
        print(f"  ID: {sub.get('id', '')}")
        print(f"  URL: {sub.get('subtitle_url', '无')}")

    # 检查CC字幕API
    print("\n" + "=" * 80)
    print("检查CC字幕API (手动字幕):")
    print("=" * 80)

    cc_url = f"https://api.bilibili.com/x/player/wbi/v2/playurl?bvid={bvid}&cid={cid}&fnval=16"
    try:
        response = requests.get(cc_url, headers=headers, cookies=cookies, timeout=10)
        cc_data = response.json()

        if cc_data.get('code') == 0:
            playurl_data = cc_data.get('data', {})
            dash_data = playurl_data.get('dash', {})
            subtitles = dash_data.get('subtitles', [])

            print(f"找到 {len(subtitles)} 个CC字幕:")

            for idx, sub in enumerate(subtitles):
                print(f"\nCC字幕 {idx + 1}:")
                print(f"  语言: {sub.get('lan_doc', '未知')}")
                print(f"  语言代码: {sub.get('lang_code', '')}")
                print(f"  URL: {sub.get('sub_url', '无')}")
        else:
            print(f"未找到CC字幕: {cc_data.get('message')}")
    except Exception as e:
        print(f"✗ 检查CC字幕失败: {e}")


if __name__ == "__main__":
    BVID = "BV1QbruBUExb"

    print(f"开始检查视频字幕: {BVID}")
    print("=" * 80 + "\n")

    cookies = load_cookies()
    check_subtitle_types(BVID, cookies)
