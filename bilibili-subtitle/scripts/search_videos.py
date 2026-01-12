#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频搜索工具
根据关键词搜索B站视频，并按播放量、点赞数等数据排序
"""

import json
import sys
import io
import requests
from datetime import datetime

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.bilibili.com',
    'Accept': 'application/json',
}


def search_videos(keyword: str, order: str = 'click', page_size: int = 20) -> list:
    """
    搜索B站视频

    Args:
        keyword: 搜索关键词
        order: 排序方式
               - 'click': 按播放量排序（最多播放）
               - 'pubdate': 按发布时间排序（最新发布）
               - 'dm': 按弹幕数排序
               - 'stow': 按收藏数排序
               - 'scores': 按评分排序
        page_size: 每页结果数量（1-50）

    Returns:
        list: 视频列表
    """
    # B站搜索API
    search_url = "https://api.bilibili.com/x/web-interface/search/all"

    # 映射排序方式到API参数
    order_mapping = {
        'click': 'totalrank',      # 综合排序
        'pubdate': 'pubdate',      # 最新发布
        'dm': 'dm',                # 弹幕数
        'stow': 'stow',            # 收藏数
        'scores': 'scores'         # 评分
    }

    order_param = order_mapping.get(order, 'totalrank')

    try:
        params = {
            'keyword': keyword,
            'search_type': 'video',  # 搜索视频
            'order': order_param,
            'page': 1,
            'page_size': min(page_size, 50)
        }

        response = requests.get(search_url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            print(f"✗ 搜索API错误: {data.get('message')}")
            return []

        # 解析搜索结果
        result = data.get('data', {}).get('result', [])

        if not result:
            print(f"✗ 未找到相关视频")
            return []

        videos = []
        for item in result:
            # 提取视频信息（B站搜索返回的是HTML格式，需要解析）
            video_info = parse_video_info(item)
            if video_info:
                videos.append(video_info)

        return videos

    except Exception as e:
        print(f"✗ 搜索失败: {e}")
        return []


def parse_video_info(item: dict) -> dict:
    """
    解析视频信息

    Args:
        item: 原始视频数据

    Returns:
        dict: 解析后的视频信息
    """
    try:
        # B站搜索API返回的标题是HTML格式，需要提取文本
        title = item.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')

        # 提取其他信息
        return {
            'bvid': item.get('bvid', ''),
            'title': title,
            'description': item.get('description', ''),
            'author': item.get('author', ''),
            'play': item.get('play', 0),           # 播放量
            'video_review': item.get('video_review', 0),  # 弹幕数
            'favorites': item.get('favorites', 0), # 收藏数
            'like': item.get('like', 0),          # 点赞数（部分视频不显示）
            'duration': item.get('duration', ''),  # 时长
            'pubdate': item.get('pubdate', 0),    # 发布时间戳
            'tag': item.get('tag', ''),            # 标签
            'pic': item.get('pic', '')             # 封面图片
        }
    except Exception as e:
        print(f"  ✗ 解析视频信息失败: {e}")
        return None


def format_duration(duration: str) -> str:
    """
    格式化时长显示

    Args:
        duration: 原始时长字符串（如 "12:34"）

    Returns:
        str: 格式化的时长
    """
    if not duration:
        return "未知"

    try:
        parts = duration.split(':')
        if len(parts) == 2:
            return f"{parts[0]}分{parts[1]}秒"
        elif len(parts) == 3:
            return f"{parts[0]}时{parts[1]}分{parts[2]}秒"
        else:
            return duration
    except:
        return duration


def format_number(num: int) -> str:
    """
    格式化数字显示

    Args:
        num: 数字

    Returns:
        str: 格式化的数字
    """
    if num >= 100000000:
        return f"{num / 100000000:.1f}亿"
    elif num >= 10000:
        return f"{num / 10000:.1f}万"
    else:
        return str(num)


def format_timestamp(timestamp: int) -> str:
    """
    格式化时间戳

    Args:
        timestamp: Unix时间戳

    Returns:
        str: 格式化的日期时间
    """
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return "未知时间"


def display_videos(videos: list, top_n: int = 10):
    """
    显示视频列表

    Args:
        videos: 视频列表
        top_n: 显示前N个视频
    """
    if not videos:
        print("✗ 没有找到视频")
        return

    print(f"\n找到 {len(videos)} 个视频，显示前 {min(top_n, len(videos))} 个：")
    print("=" * 100)

    for idx, video in enumerate(videos[:top_n], 1):
        print(f"\n【{idx}】{video['title']}")
        print(f"    BV号: {video['bvid']}")
        print(f"    UP主: {video['author']}")
        print(f"    时长: {format_duration(video['duration'])}")
        print(f"    播放: {format_number(video['play'])} | "
              f"弹幕: {format_number(video['video_review'])} | "
              f"收藏: {format_number(video['favorites'])}")
        if video.get('like'):
            print(f"    点赞: {format_number(video['like'])}")
        print(f"    发布: {format_timestamp(video['pubdate'])}")

        # 显示视频描述（前100个字符）
        if video.get('description'):
            desc = video['description'][:100]
            if len(video['description']) > 100:
                desc += "..."
            print(f"    简介: {desc}")

    print("\n" + "=" * 100)


def select_videos(videos: list, indices: list) -> list:
    """
    根据索引选择视频

    Args:
        videos: 视频列表
        indices: 索引列表（1-based）

    Returns:
        list: 选中的视频列表
    """
    selected = []
    for idx in indices:
        if 1 <= idx <= len(videos):
            selected.append(videos[idx - 1])
        else:
            print(f"⚠️  索引 {idx} 超出范围，已跳过")
    return selected


def save_bvid_list(videos: list, filename: str):
    """
    保存BV号列表到文件

    Args:
        videos: 视频列表
        filename: 输出文件名
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for video in videos:
                f.write(f"{video['bvid']}\n")
        print(f"\n✓ BV号列表已保存到: {filename}")
    except Exception as e:
        print(f"\n✗ 保存BV号列表失败: {e}")


def save_search_results(videos: list, filename: str):
    """
    保存搜索结果为JSON文件

    Args:
        videos: 视频列表
        filename: 输出文件名
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
        print(f"✓ 搜索结果已保存到: {filename}")
    except Exception as e:
        print(f"✗ 保存搜索结果失败: {e}")


if __name__ == "__main__":
    # 示例使用
    if len(sys.argv) < 2:
        print("使用方法: python search_videos.py <关键词> [排序方式] [显示数量]")
        print("\n排序方式:")
        print("  click   - 按播放量排序（默认）")
        print("  pubdate - 按发布时间排序")
        print("  dm      - 按弹幕数排序")
        print("  stow    - 按收藏数排序")
        print("\n示例:")
        print("  python search_videos.py 拍立得测评")
        print("  python search_videos.py 拍立得测评 pubdate 15")
        sys.exit(1)

    keyword = sys.argv[1]
    order = sys.argv[2] if len(sys.argv) > 2 else 'click'
    top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    print("=" * 100)
    print(f"B站视频搜索工具")
    print("=" * 100)
    print(f"关键词: {keyword}")
    print(f"排序方式: {order}")
    print("\n正在搜索...")

    # 搜索视频
    videos = search_videos(keyword, order=order, page_size=50)

    if videos:
        # 显示视频列表
        display_videos(videos, top_n=top_n)

        # 保存搜索结果
        result_filename = f"search_results_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_search_results(videos, result_filename)

        # 询问是否保存BV号列表
        print(f"\n是否要保存前10个视频的BV号列表？")
        print(f"保存后可用于批量提取字幕：python extract_batch.py")
        print(f"\nBV号列表：")
        for i, video in enumerate(videos[:10], 1):
            print(f"  {i}. {video['bvid']} - {video['title'][:50]}")
