#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量提取B站拍立得选购及测评视频字幕
提取近3个月最火的10条拍立得视频字幕并保存为Markdown格式
"""

import json
import sys
import io
import requests
import time
import os
from typing import List, Dict

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class BilibiliSubtitleExtractor:
    """B站字幕提取器"""

    def __init__(self, cookies_file: str = "cookies_template.json"):
        """初始化"""
        self.cookies = self.load_cookies(cookies_file)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com',
            'Accept': 'application/json',
        }

    def load_cookies(self, cookies_file: str) -> dict:
        """加载cookies"""
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"警告: Cookie文件 {cookies_file} 不存在，将不使用cookies")
            return {}

    def extract_subtitle(self, bvid: str) -> dict:
        """提取单个视频字幕"""
        print(f"\n{'='*80}")
        print(f"开始提取: {bvid}")
        print('='*80)

        # 获取视频信息
        info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        try:
            response = requests.get(info_url, headers=self.headers, cookies=self.cookies, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('code') != 0:
                return {"error": f"API错误: {data.get('message')}", "bvid": bvid}

            video_data = data.get('data', {})
            title = video_data.get('title', '未知标题')
            cid = video_data.get('cid', 0)

            # 获取视频统计信息
            stat = video_data.get('stat', {})
            view = stat.get('view', 0)  # 播放量
            like = stat.get('like', 0)   # 点赞数
            coin = stat.get('coin', 0)   # 投币数
            collect = stat.get('favorite', 0)  # 收藏数

            print(f"✓ 标题: {title}")
            print(f"  播放: {view:,} | 点赞: {like:,} | 投币: {coin:,} | 收藏: {collect:,}")

        except Exception as e:
            return {"error": f"获取视频信息失败: {e}", "bvid": bvid}

        # 获取字幕列表
        subtitle_url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
        try:
            response = requests.get(subtitle_url, headers=self.headers, cookies=self.cookies, timeout=10)
            response.raise_for_status()
            player_data = response.json()

            if player_data.get('code') != 0:
                return {"error": f"播放器API错误: {player_data.get('message')}", "bvid": bvid}

            subtitle_info = player_data.get('data', {}).get('subtitle', {})
            subtitles_list = subtitle_info.get('subtitles', [])

            if not subtitles_list:
                print("✗ 该视频没有字幕")
                return {
                    "bvid": bvid,
                    "title": title,
                    "error": "该视频没有字幕",
                    "view": view,
                    "like": like,
                    "coin": coin,
                    "collect": collect
                }

            print(f"✓ 找到 {len(subtitles_list)} 个字幕轨道")

            # 提取所有字幕
            subtitles_data = []
            for idx, sub in enumerate(subtitles_list):
                lang = sub.get('lan_doc', '未知语言')
                subtitle_id = sub.get('id', '')
                sub_url = sub.get('subtitle_url', '')

                print(f"  正在提取: {lang}")

                if sub_url:
                    try:
                        # 处理URL
                        if sub_url.startswith('//'):
                            sub_url = 'https:' + sub_url

                        sub_response = requests.get(sub_url, headers=self.headers, cookies=self.cookies, timeout=10)
                        sub_response.raise_for_status()
                        subtitle_content = sub_response.json()

                        # 解析字幕条目
                        entries = subtitle_content.get('body', [])
                        subtitle_text = []

                        for entry in entries:
                            from_time = entry.get('from', 0)
                            to_time = entry.get('to', 0)
                            content = entry.get('content', '')

                            subtitle_text.append({
                                "start": self.format_time(from_time),
                                "end": self.format_time(to_time),
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

                        print(f"    ✓ 提取了 {len(entries)} 条字幕")

                    except Exception as e:
                        print(f"    ✗ 提取失败: {e}")
                        continue

            # 如果没有成功提取任何字幕
            if not subtitles_data:
                return {
                    "bvid": bvid,
                    "title": title,
                    "error": "无法提取字幕内容",
                    "view": view,
                    "like": like,
                    "coin": coin,
                    "collect": collect
                }

            return {
                "bvid": bvid,
                "title": title,
                "cid": cid,
                "subtitle_count": len(subtitles_data),
                "subtitles": subtitles_data,
                "view": view,
                "like": like,
                "coin": coin,
                "collect": collect
            }

        except Exception as e:
            return {"error": f"获取字幕失败: {e}", "bvid": bvid}

    def format_time(self, seconds: float) -> str:
        """格式化时间显示"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    def save_to_markdown(self, data: dict, filename: str):
        """保存为Markdown格式"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # 写入头部信息
                f.write(f"# {data.get('title', '未知标题')}\n\n")
                f.write(f"**BV号**: {data.get('bvid', '')}\n\n")
                f.write(f"**播放量**: {data.get('view', 0):,}\n\n")
                f.write(f"**点赞数**: {data.get('like', 0):,}\n\n")
                f.write(f"**投币数**: {data.get('coin', 0):,}\n\n")
                f.write(f"**收藏数**: {data.get('collect', 0):,}\n\n")

                if "error" in data:
                    f.write(f"**错误**: {data.get('error')}\n\n")
                    print(f"✓ 已保存到: {filename}")
                    return

                subtitle_track = data.get('subtitles', [{}])[0]
                f.write(f"**字幕语言**: {subtitle_track.get('language', '未知')}\n\n")
                f.write(f"**字幕条数**: {len(subtitle_track.get('subtitles', []))} 条\n\n")
                f.write("---\n\n")

                # 保存第一个字幕轨道
                subtitles = subtitle_track.get('subtitles', [])
                for entry in subtitles:
                    f.write(f"{entry['text']}\n")

            print(f"✓ 已保存到: {filename}")
        except Exception as e:
            print(f"✗ 保存文件失败: {e}")


def main():
    """主函数"""
    print("="*80)
    print("B站拍立得选购及测评视频字幕批量提取")
    print("="*80)

    # 前10个热门拍立得视频BV号（基于B站搜索结果）
    video_list = [
        "BV1BW4y1A7Tc",  # 拍立得选购指南-富士mini系列拍立得机型差异及成像画质颜色差异细致对比
        "BV1Rj421R7qK",  # 入手需「慎重」！富士SQ方型拍立得全线产品盘点及理性选购建议
        "BV1s54y1h7JP",  # 2021宝丽来选购指南 穿越23年的拍立得对决从性价比到功能全面剖析
        "BV1N4411W7q6",  # Polaroid宝丽来||使用两个月后感受//拍立得选购指南//拍立得测评
        "BV1HCJHzwEXR",  # 富士&宝丽来拍立得该如何选择？
        "BV1b5411t7TG",  # VLOG.033教你如何挑选最具性价比的拍立得或者宝丽来-横评五款拍立得或者宝丽来
        "BV1fR4y137NY",  # 新手必备|超全网红拍立得选购指南，都是我那废片换来的！
        "BV1Tt411C77E",  # 「纯干货」各个价位最全礼物挑选指南 ／送女友礼物单品推荐 / 拍立得&球鞋&Sephora套盒&more
        "BV1Qe411x7QE",  # 【拍立得评测】中字-Lomography Instant Wide宽幅拍立得相机 宝丽来外的另一种选择
        "BV1FcYfzYEhV",  # mini12 vs miniSE：拍立得选择指南，一篇看懂~
    ]

    print(f"\n准备提取 {len(video_list)} 个视频的字幕")
    print(f"保存目录: skills/skills/bilibili-subtitle/pailide/\n")

    # 确保目录存在
    output_dir = "skills/skills/bilibili-subtitle/pailide"
    os.makedirs(output_dir, exist_ok=True)

    extractor = BilibiliSubtitleExtractor()
    results = []

    for idx, bvid in enumerate(video_list, 1):
        print(f"\n[{idx}/{len(video_list)}] 正在处理 {bvid}...")
        result = extractor.extract_subtitle(bvid)

        # 生成文件名（使用BV号）
        filename = os.path.join(output_dir, f"subtitle_{bvid}.md")
        extractor.save_to_markdown(result, filename)
        results.append(result)

        # 避免请求过快
        time.sleep(1.5)

    # 统计结果
    print(f"\n{'='*80}")
    print("批量提取完成!")
    print('='*80)

    success_count = sum(1 for r in results if "error" not in r)
    failed_count = len(results) - success_count

    print(f"\n总计: {len(video_list)} 个视频")
    print(f"✓ 成功: {success_count} 个")
    print(f"✗ 失败: {failed_count} 个")

    # 列出失败的
    if failed_count > 0:
        print("\n失败的视频:")
        for r in results:
            if "error" in r:
                print(f"  - {r.get('bvid')}: {r.get('error')}")

    print(f"\n所有字幕文件已保存到: {output_dir}")


if __name__ == "__main__":
    main()
