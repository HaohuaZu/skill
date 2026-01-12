#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频字幕提取工具
用于提取指定B站视频的字幕并保存为JSON和TXT格式
"""

import json
import sys
import io
import requests
import re

# 设置标准输出编码为UTF-8，解决Windows终端编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 请求头配置，模拟浏览器访问
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

        print(f"✓ 成功获取视频信息: {title}")
        print(f"  CID: {cid}")

    except Exception as e:
        print(f"✗ 获取视频信息失败: {e}")
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

        print(f"✓ 找到 {len(subtitles_list)} 个字幕轨道")

        if not subtitles_list:
            print("✗ 该视频没有可用的字幕")
            return {"error": "该视频没有可用的字幕"}

        # 提取所有字幕
        subtitles_data = []
        for idx, sub in enumerate(subtitles_list):
            lang = sub.get('lan_doc', '未知语言')
            subtitle_id = sub.get('id', '')
            sub_url = sub.get('subtitle_url', '')

            print(f"\n正在提取字幕 {idx + 1}/{len(subtitles_list)}: {lang}")
            print(f"  字幕ID: {subtitle_id}")
            print(f"  字幕URL: {sub_url}")

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

                    print(f"  ✓ 提取了 {len(entries)} 条字幕")

                except Exception as e:
                    print(f"  ✗ 提取字幕失败: {e}")
                    continue

        return {
            "bvid": bvid,
            "title": title,
            "cid": cid,
            "subtitle_count": len(subtitles_data),
            "subtitles": subtitles_data
        }

    except Exception as e:
        print(f"✗ 获取字幕失败: {e}")
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


def save_subtitle_to_json(data: dict, filename: str):
    """
    将字幕数据保存为JSON文件

    Args:
        data: 字幕数据字典
        filename: 输出文件名
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 字幕已保存到: {filename}")
    except Exception as e:
        print(f"\n✗ 保存JSON文件失败: {e}")


def save_subtitle_to_txt(data: dict, filename: str):
    """
    将字幕数据保存为TXT文件（纯文本格式）

    Args:
        data: 字幕数据字典
        filename: 输出文件名
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
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

        print(f"✓ 字幕已保存到: {filename}")
    except Exception as e:
        print(f"✗ 保存TXT文件失败: {e}")


def save_subtitle_to_srt(data: dict, filename: str):
    """
    将字幕数据保存为SRT文件（标准字幕格式）

    Args:
        data: 字幕数据字典
        filename: 输出文件名
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # 只保存第一个字幕轨道（通常是中文）
            subtitle_track = data.get('subtitles', [{}])[0]
            lang = subtitle_track.get('language', '未知')

            f.write(f"# 视频标题: {data.get('title', '')}\n")
            f.write(f"# BV号: {data.get('bvid', '')}\n")
            f.write(f"# 字幕语言: {lang}\n\n")

            for idx, entry in enumerate(subtitle_track.get('subtitles', []), 1):
                f.write(f"{idx}\n")
                f.write(f"{entry['start']} --> {entry['end']}\n")
                f.write(f"{entry['text']}\n\n")

        print(f"✓ 字幕已保存到: {filename}")
    except Exception as e:
        print(f"✗ 保存SRT文件失败: {e}")


if __name__ == "__main__":
    # 视频BV号
    BVID = "BV1Hwi4BYEJz"

    print(f"开始提取视频字幕: {BVID}")
    print("=" * 80)

    # 提取字幕
    result = extract_subtitle(BVID)

    if "error" not in result:
        # 保存为JSON格式
        json_filename = f"bilibili_subtitle_{BVID}.json"
        save_subtitle_to_json(result, json_filename)

        # 保存为TXT格式
        txt_filename = f"bilibili_subtitle_{BVID}.txt"
        save_subtitle_to_txt(result, txt_filename)

        # 保存为SRT格式
        srt_filename = f"bilibili_subtitle_{BVID}.srt"
        save_subtitle_to_srt(result, srt_filename)

        print("\n" + "=" * 80)
        print("字幕提取完成!")
        print(f"共提取 {result.get('subtitle_count', 0)} 个字幕轨道")
        track_info = ", ".join([f"{track.get('language', '未知')}" for track in result.get('subtitles', [])])
        print(f"语言: {track_info}")
    else:
        print(f"\n字幕提取失败: {result.get('error')}")
