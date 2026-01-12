#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频字幕批量提取工具
用于批量提取多个B站视频的字幕并保存为多种格式
"""

import json
import sys
import io
import requests
import time
from pathlib import Path

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.bilibili.com',
    'Accept': 'application/json',
}


def extract_subtitle(bvid: str) -> dict:
    """
    提取B站视频字幕

    Args:
        bvid: B站视频BV号

    Returns:
        dict: 包含视频信息和字幕内容的字典
    """
    # 获取视频信息
    info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        response = requests.get(info_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            return {"error": f"API错误: {data.get('message')}"}

        video_data = data.get('data', {})
        title = video_data.get('title', '未知标题')
        cid = video_data.get('cid', 0)

        print(f"  ✓ 成功获取视频信息: {title}")

    except Exception as e:
        print(f"  ✗ 获取视频信息失败: {e}")
        return {"error": str(e)}

    # 获取字幕列表
    subtitle_url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
    try:
        response = requests.get(subtitle_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_data = response.json()

        if player_data.get('code') != 0:
            return {"error": f"播放器API错误: {player_data.get('message')}"}

        subtitle_info = player_data.get('data', {}).get('subtitle', {})
        subtitles_list = subtitle_info.get('subtitles', [])

        print(f"  ✓ 找到 {len(subtitles_list)} 个字幕轨道")

        if not subtitles_list:
            print(f"  ✗ 该视频没有可用的字幕")
            return {"error": "该视频没有可用的字幕"}

        # 提取所有字幕
        subtitles_data = []
        for sub in subtitles_list:
            lang = sub.get('lan_doc', '未知语言')
            subtitle_id = sub.get('id', '')
            sub_url = sub.get('subtitle_url', '')

            if sub_url:
                try:
                    # 下载字幕内容
                    sub_response = requests.get(sub_url, headers=HEADERS, timeout=10)
                    sub_response.raise_for_status()
                    subtitle_content = sub_response.json()

                    # 解析字幕条目
                    entries = subtitle_content.get('body', [])

                    subtitle_text = []
                    for entry in entries:
                        from_time = entry.get('from', 0)
                        to_time = entry.get('to', 0)
                        content = entry.get('content', '')

                        # 格式化时间显示
                        from_str = format_time(from_time)
                        to_str = format_time(to_time)

                        subtitle_text.append({
                            "start": from_str,
                            "end": to_str,
                            "start_seconds": from_time,
                            "end_seconds": to_time,
                            "text": content
                        })

                    subtitles_data.append({
                        "language": lang,
                        "language_code": sub.get('lan', ''),
                        "id": subtitle_id,
                        "subtitles": subtitle_text
                    })

                except Exception as e:
                    print(f"    ✗ 提取字幕失败: {e}")
                    continue

        return {
            "bvid": bvid,
            "title": title,
            "cid": cid,
            "subtitle_count": len(subtitles_data),
            "subtitles": subtitles_data
        }

    except Exception as e:
        print(f"  ✗ 获取字幕失败: {e}")
        return {"error": str(e)}


def format_time(seconds: float) -> str:
    """
    将秒数转换为时间格式 HH:MM:SS.mmm

    Args:
        seconds: 秒数

    Returns:
        str: 格式化的时间字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def save_subtitle(data: dict, output_dir: str = "."):
    """
    保存字幕为所有格式

    Args:
        data: 字幕数据字典
        output_dir: 输出目录
    """
    if "error" in data:
        return

    bvid = data.get('bvid', '')
    if not bvid:
        return

    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 保存为JSON格式
    json_filename = output_path / f"bilibili_subtitle_{bvid}.json"
    try:
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ JSON: {json_filename}")
    except Exception as e:
        print(f"  ✗ 保存JSON失败: {e}")

    # 保存为TXT格式
    txt_filename = output_path / f"bilibili_subtitle_{bvid}.txt"
    try:
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(f"视频标题: {data.get('title', '')}\n")
            f.write(f"BV号: {data.get('bvid', '')}\n")
            f.write(f"字幕数量: {data.get('subtitle_count', 0)}\n")
            f.write("=" * 80 + "\n\n")

            for idx, subtitle_track in enumerate(data.get('subtitles', [])):
                f.write(f"字幕轨道 {idx + 1} [{subtitle_track.get('language', '未知')}]\n")
                f.write("-" * 80 + "\n")

                for entry in subtitle_track.get('subtitles', []):
                    f.write(f"[{entry['start']} -> {entry['end']}] {entry['text']}\n")

                f.write("\n")
        print(f"  ✓ TXT: {txt_filename}")
    except Exception as e:
        print(f"  ✗ 保存TXT失败: {e}")

    # 保存为SRT格式
    srt_filename = output_path / f"bilibili_subtitle_{bvid}.srt"
    try:
        with open(srt_filename, 'w', encoding='utf-8') as f:
            subtitle_track = data.get('subtitles', [{}])[0]
            lang = subtitle_track.get('language', '未知')

            f.write(f"# 视频标题: {data.get('title', '')}\n")
            f.write(f"# BV号: {data.get('bvid', '')}\n")
            f.write(f"# 字幕语言: {lang}\n\n")

            for idx, entry in enumerate(subtitle_track.get('subtitles', []), 1):
                f.write(f"{idx}\n")
                f.write(f"{entry['start']} --> {entry['end']}\n")
                f.write(f"{entry['text']}\n\n")
        print(f"  ✓ SRT: {srt_filename}")
    except Exception as e:
        print(f"  ✗ 保存SRT失败: {e}")

    # 保存为Markdown格式
    md_filename = output_path / f"bilibili_subtitle_{bvid}.md"
    try:
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(f"# {data.get('title', '未知标题')}\n\n")
            f.write(f"**BV号**: {data.get('bvid', '')}\n\n")
            f.write(f"**字幕数量**: {data.get('subtitle_count', 0)}\n\n")
            f.write("---\n\n")

            for idx, subtitle_track in enumerate(data.get('subtitles', [])):
                f.write(f"## 字幕轨道 {idx + 1} - {subtitle_track.get('language', '未知')}\n\n")

                for entry in subtitle_track.get('subtitles', []):
                    f.write(f"**[{entry['start']} - {entry['end']}]** {entry['text']}\n\n")
        print(f"  ✓ Markdown: {md_filename}")
    except Exception as e:
        print(f"  ✗ 保存Markdown失败: {e}")


def load_video_list(file_path: str) -> list:
    """
    从文件加载视频列表

    Args:
        file_path: 视频列表文件路径

    Returns:
        list: 视频BV号列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            bvids = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return bvids
    except Exception as e:
        print(f"✗ 读取视频列表失败: {e}")
        return []


if __name__ == "__main__":
    # 视频列表文件
    VIDEO_LIST_FILE = "video_list.txt"

    # 输出目录
    OUTPUT_DIR = "subtitles"

    print("B站视频字幕批量提取工具")
    print("=" * 80)

    # 加载视频列表
    video_list = load_video_list(VIDEO_LIST_FILE)

    if not video_list:
        print(f"\n✗ 未找到视频列表，请在 {VIDEO_LIST_FILE} 中添加视频BV号")
        print("文件格式：每行一个BV号，支持 # 开头的注释行")
        sys.exit(1)

    print(f"\n共找到 {len(video_list)} 个视频需要处理\n")

    # 处理每个视频
    success_count = 0
    fail_count = 0

    for idx, bvid in enumerate(video_list, 1):
        print(f"\n[{idx}/{len(video_list)}] 处理视频: {bvid}")
        print("-" * 80)

        result = extract_subtitle(bvid)

        if "error" not in result:
            save_subtitle(result, OUTPUT_DIR)
            success_count += 1

            # 添加延迟，避免请求过于频繁
            if idx < len(video_list):
                print(f"\n  等待2秒后处理下一个视频...")
                time.sleep(2)
        else:
            fail_count += 1

    # 输出统计信息
    print("\n" + "=" * 80)
    print("批量提取完成!")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    print(f"总计: {len(video_list)} 个")
    print(f"\n字幕文件保存在: {OUTPUT_DIR}/")
