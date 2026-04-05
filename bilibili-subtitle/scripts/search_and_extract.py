#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能搜索并提取字幕
一站式工具：搜索视频 → 展示排序结果 → 选择视频 → 提取字幕
"""

import json
import sys
import io
import requests
from datetime import datetime
import subprocess

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.bilibili.com',
    'Accept': 'application/json',
}


def search_videos(keyword: str, order: str = 'click', page_size: int = 30) -> list:
    """搜索B站视频"""
    search_url = "https://api.bilibili.com/x/web-interface/search/all"

    order_mapping = {
        'click': 'totalrank',
        'pubdate': 'pubdate',
        'dm': 'dm',
        'stow': 'stow',
        'scores': 'scores'
    }

    order_param = order_mapping.get(order, 'totalrank')

    try:
        params = {
            'keyword': keyword,
            'search_type': 'video',
            'order': order_param,
            'page': 1,
            'page_size': min(page_size, 50)
        }

        response = requests.get(search_url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            return []

        result = data.get('data', {}).get('result', [])
        videos = []

        for item in result:
            title = item.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')
            videos.append({
                'bvid': item.get('bvid', ''),
                'title': title,
                'author': item.get('author', ''),
                'play': item.get('play', 0),
                'video_review': item.get('video_review', 0),
                'favorites': item.get('favorites', 0),
                'like': item.get('like', 0),
                'duration': item.get('duration', ''),
                'pubdate': item.get('pubdate', 0),
            })

        return videos

    except Exception as e:
        print(f"✗ 搜索失败: {e}")
        return []


def format_number(num: int) -> str:
    """格式化数字显示"""
    if num >= 100000000:
        return f"{num / 100000000:.1f}亿"
    elif num >= 10000:
        return f"{num / 10000:.1f}万"
    else:
        return str(num)


def format_timestamp(timestamp: int) -> str:
    """格式化时间戳"""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d')
    except:
        return "未知"


def display_videos(videos: list):
    """显示视频列表"""
    print(f"\n找到 {len(videos)} 个相关视频：")
    print("=" * 120)

    for idx, video in enumerate(videos, 1):
        print(f"\n【{idx}】{video['title'][:60]}")
        print(f"    BV号: {video['bvid']}")
        print(f"    UP主: {video['author']}")
        print(f"    播放: {format_number(video['play'])} | "
              f"弹幕: {format_number(video['video_review'])} | "
              f"收藏: {format_number(video['favorites'])}")
        print(f"    发布: {format_timestamp(video['pubdate'])}")

    print("\n" + "=" * 120)


def extract_subtitle_for_video(bvid: str):
    """提取单个视频的字幕"""
    extract_script = "extract_single.py"

    try:
        # 读取提取脚本
        with open(extract_script, 'r', encoding='utf-8') as f:
            script_content = f.read()

        # 替换BVID
        modified_script = script_content.replace(
            'BVID = "BV1Hwi4BYEJz"',
            f'BVID = "{bvid}"'
        )

        # 保存临时脚本
        temp_script = f"temp_extract_{bvid}.py"
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(modified_script)

        # 运行脚本
        print(f"\n正在提取视频 {bvid} 的字幕...")
        print("-" * 80)
        result = subprocess.run(
            [sys.executable, temp_script],
            capture_output=False,
            text=True
        )

        # 删除临时脚本
        import os
        os.remove(temp_script)

        return result.returncode == 0

    except Exception as e:
        print(f"✗ 提取字幕失败: {e}")
        return False


def interactive_select(videos: list):
    """交互式选择视频"""
    print("\n请选择要提取字幕的视频：")
    print("  - 输入单个数字（如：1）选择单个视频")
    print("  - 输入多个数字用逗号分隔（如：1,3,5）选择多个视频")
    print("  - 输入范围（如：1-5）选择连续多个视频")
    print("  - 输入 'all' 提取所有视频的字幕")
    print("  - 输入 'q' 退出\n")

    user_input = input("您的选择: ").strip()

    if user_input.lower() == 'q':
        return []

    if user_input.lower() == 'all':
        return videos

    selected_videos = []

    try:
        # 处理范围选择（如 1-5）
        if '-' in user_input:
            start, end = user_input.split('-')
            indices = list(range(int(start), int(end) + 1))
        # 处理多个数字（如 1,3,5）
        elif ',' in user_input:
            indices = [int(x.strip()) for x in user_input.split(',')]
        # 处理单个数字
        else:
            indices = [int(user_input)]

        # 根据索引选择视频
        for idx in indices:
            if 1 <= idx <= len(videos):
                selected_videos.append(videos[idx - 1])
            else:
                print(f"⚠️  索引 {idx} 超出范围，已跳过")

    except ValueError:
        print("✗ 输入格式错误，请重新运行")
        return []

    return selected_videos


if __name__ == "__main__":
    print("=" * 120)
    print("B站智能字幕提取工具")
    print("=" * 120)

    # 获取搜索关键词
    if len(sys.argv) < 2:
        keyword = input("\n请输入搜索关键词（如：拍立得测评）: ").strip()
        if not keyword:
            print("✗ 关键词不能为空")
            sys.exit(1)
    else:
        keyword = sys.argv[1]

    # 获取排序方式
    print("\n排序方式：")
    print("  1. 按播放量（默认）")
    print("  2. 按发布时间")
    print("  3. 按弹幕数")
    print("  4. 按收藏数")

    order_input = input("\n请选择排序方式（直接回车使用默认）: ").strip()
    order_mapping = {
        '': 'click',
        '1': 'click',
        '2': 'pubdate',
        '3': 'dm',
        '4': 'stow'
    }
    order = order_mapping.get(order_input, 'click')

    # 搜索视频
    print(f"\n正在搜索「{keyword}」相关视频...")
    videos = search_videos(keyword, order=order, page_size=30)

    if not videos:
        print("✗ 未找到相关视频")
        sys.exit(1)

    # 显示搜索结果
    display_videos(videos)

    # 交互式选择视频
    selected_videos = interactive_select(videos)

    if not selected_videos:
        print("已取消")
        sys.exit(0)

    print(f"\n已选择 {len(selected_videos)} 个视频")
    print("=" * 120)

    # 批量提取字幕
    success_count = 0
    fail_count = 0

    for idx, video in enumerate(selected_videos, 1):
        print(f"\n[{idx}/{len(selected_videos)}] 处理: {video['title'][:50]}")
        print(f"BV号: {video['bvid']}")

        if extract_subtitle_for_video(video['bvid']):
            success_count += 1
            print(f"✓ 字幕提取完成")
        else:
            fail_count += 1
            print(f"✗ 字幕提取失败")

        # 添加延迟
        if idx < len(selected_videos):
            import time
            print(f"\n等待2秒后继续...")
            time.sleep(2)

    # 显示统计
    print("\n" + "=" * 120)
    print("批量提取完成！")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    print("=" * 120)
