#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频字幕批量提取工具
功能:
1. 手动输入BV号批量提取
2. 关键词搜索视频并提取字幕
3. 智能筛选优质视频
"""

import json
import sys
import io
import requests
import time
from typing import List, Dict
import re

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
            print(f"✗ Cookie文件 {cookies_file} 不存在")
            sys.exit(1)

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

    def search_videos(self, keyword: str, max_results: int = 10) -> List[Dict]:
        """搜索视频"""
        print(f"\n{'='*80}")
        print(f"搜索关键词: {keyword}")
        print('='*80)

        search_url = "https://api.bilibili.com/x/web-interface/search/type"
        params = {
            'search_type': 'video',
            'keyword': keyword,
            'page': 1,
        }

        try:
            response = requests.get(search_url, headers=self.headers, cookies=self.cookies,
                                  params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get('code') != 0:
                print(f"✗ 搜索失败: {result.get('message')}")
                return []

            data = result.get('data', {})
            videos = data.get('result', [])[:max_results]

            print(f"✓ 找到 {len(videos)} 个视频\n")

            formatted_videos = []
            for idx, video in enumerate(videos, 1):
                # 从title中提取BV号
                title = video.get('title', '')
                bvid_match = re.search(r'BV[\w]+', title)
                bvid = bvid_match.group(0) if bvid_match else video.get('bvid', '')

                # 获取视频信息
                author = video.get('author', '')
                play = video.get('play', 0)
                duration = video.get('duration', '')
                description = video.get('description', '')[:100]

                formatted_videos.append({
                    'bvid': bvid,
                    'title': title,
                    'author': author,
                    'play': play,
                    'duration': duration,
                    'description': description
                })

                print(f"{idx}. {title}")
                print(f"   BV: {bvid}")
                print(f"   UP主: {author} | 播放: {play:,} | 时长: {duration}")
                print(f"   简介: {description}...")
                print()

            return formatted_videos

        except Exception as e:
            print(f"✗ 搜索失败: {e}")
            return []


def main():
    """主函数"""
    print("="*80)
    print("B站视频字幕批量提取工具")
    print("="*80)

    extractor = BilibiliSubtitleExtractor()

    print("\n请选择功能:")
    print("1. 手动输入BV号")
    print("2. 搜索视频并提取字幕")
    print("3. 批量输入BV号")

    choice = input("\n请输入选项 (1/2/3): ").strip()

    if choice == "1":
        # 单个BV号
        bvid = input("请输入BV号 (例如: BV1ypsAzhEL9): ").strip()
        if not bvid.startswith('BV'):
            bvid = 'BV' + bvid

        result = extractor.extract_subtitle(bvid)
        filename = f"subtitle_{bvid}.md"
        extractor.save_to_markdown(result, filename)

        if "error" not in result:
            print(f"\n✓ 字幕提取完成!")
            print(f"  标题: {result.get('title')}")
            print(f"  字幕轨道: {result.get('subtitle_count')} 个")
        else:
            print(f"\n✗ {result.get('error')}")

    elif choice == "2":
        # 搜索视频
        keyword = input("请输入搜索关键词: ").strip()
        max_results = input("最多提取几个视频? (默认5个): ").strip()
        max_results = int(max_results) if max_results else 5

        videos = extractor.search_videos(keyword, max_results)

        if not videos:
            print("✗ 未找到视频")
            return

        print(f"\n将提取以下 {len(videos)} 个视频的字幕...")
        confirm = input("是否继续? (y/n): ").strip().lower()

        if confirm == 'y':
            results = []
            for idx, video in enumerate(videos, 1):
                print(f"\n[{idx}/{len(videos)}] 正在处理...")
                result = extractor.extract_subtitle(video['bvid'])
                filename = f"subtitle_{video['bvid']}.md"
                extractor.save_to_markdown(result, filename)
                results.append(result)
                time.sleep(1)  # 避免请求过快

            # 统计
            success_count = sum(1 for r in results if "error" not in r)
            print(f"\n{'='*80}")
            print(f"提取完成! 成功: {success_count}/{len(videos)}")
            print('='*80)

    elif choice == "3":
        # 批量输入BV号
        print("\n请输入BV号 (多个BV号用逗号或空格分隔):")
        print("例如: BV1ypsAzhEL9 BV1bqi9BWE7M")
        input_text = input("> ").strip()

        # 分割BV号
        bvids = re.findall(r'BV[\w]+', input_text)

        if not bvids:
            print("✗ 未检测到有效的BV号")
            return

        print(f"\n检测到 {len(bvids)} 个BV号")

        results = []
        for idx, bvid in enumerate(bvids, 1):
            print(f"\n[{idx}/{len(bvids)}] 正在处理 {bvid}...")
            result = extractor.extract_subtitle(bvid)
            filename = f"subtitle_{bvid}.md"
            extractor.save_to_markdown(result, filename)
            results.append(result)
            time.sleep(1)

        # 统计
        success_count = sum(1 for r in results if "error" not in r)
        print(f"\n{'='*80}")
        print(f"批量提取完成! 成功: {success_count}/{len(bvids)}")
        print('='*80)

        # 列出失败的
        failed = [r.get('bvid') for r in results if "error" in r]
        if failed:
            print(f"失败的BV号: {', '.join(failed)}")

    else:
        print("✗ 无效选项")


if __name__ == "__main__":
    main()
