#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站字幕提取工具 - 支持Cookies版本
帮助说明如何获取和使用B站Cookies
"""

import json
import sys
import io
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# ============================================================================
# 使用说明
# ============================================================================
INSTRUCTIONS = """
═══════════════════════════════════════════════════════════════
                    B站Cookies获取指南
═══════════════════════════════════════════════════════════════

【方法一: 浏览器开发者工具获取】(推荐)

1. 打开Chrome/Edge浏览器,登录B站
2. 按 F12 打开开发者工具
3. 切换到 "Network"(网络) 标签
4. 刷新页面,找到任意请求
5. 在请求头中找到 "Cookie:" 字段
6. 复制整个Cookie字符串(很长的一段)

【方法二: 浏览器插件】(最简单)

1. 安装 "EditThisCookie" 或 "Cookie-Editor" 插件
2. 访问 bilibili.com 并登录
3. 点击插件图标,导出为JSON格式
4. 将导出的内容保存为 cookies.json

【重要的B站Cookies字段】

必需字段:
- SESSDATA          # 会令牌(最重要)
- bili_jct          # CSRF令牌
- DedeUserID        # 用户ID
- DedeUserID__ckMd5 # 用户ID摘要

可选字段:
- sid               # 会话ID
- buvid3            # 浏览器唯一标识

═══════════════════════════════════════════════════════════════
"""


def load_cookies_from_file(filename: str = "cookies.json") -> dict:
    """从文件加载cookies"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)

        # 如果是EditThisCookie导出的格式
        if isinstance(cookies_data, list):
            cookies = {}
            for item in cookies_data:
                cookies[item['name']] = item['value']
            return cookies

        # 如果是简单的字典格式
        return cookies_data
    except FileNotFoundError:
        print(f"❌ 未找到 {filename} 文件")
        print("\n请按以下步骤操作:")
        print("1. 将你的Cookie字符串保存到 cookies.txt 文件中")
        print("2. 或者将cookies.json文件放到当前目录")
        return None


def load_cookies_from_string(cookie_string: str) -> dict:
    """从Cookie字符串解析cookies"""
    cookies = {}
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies


def test_subtitle_with_cookies(bvid: str, cookies: dict) -> bool:
    """使用cookies测试字幕接口"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.bilibili.com',
        'Accept': 'application/json',
    }

    # 获取视频信息
    info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        response = requests.get(info_url, headers=headers, cookies=cookies, timeout=10)
        data = response.json()

        if data.get('code') != 0:
            print(f"❌ API错误: {data.get('message')}")
            return False

        video_data = data.get('data', {})
        title = video_data.get('title', '')
        cid = video_data.get('cid', 0)

        print(f"✓ 视频标题: {title}")
        print(f"✓ CID: {cid}")

        # 获取字幕
        subtitle_url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
        response = requests.get(subtitle_url, headers=headers, cookies=cookies, timeout=10)
        player_data = response.json()

        if player_data.get('code') != 0:
            print(f"❌ 播放器API错误: {player_data.get('message')}")
            return False

        subtitle_info = player_data.get('data', {}).get('subtitle', {})
        subtitles = subtitle_info.get('subtitles', [])

        print(f"\n✓ 找到 {len(subtitles)} 个字幕轨道")

        if subtitles:
            for sub in subtitles:
                print(f"  - {sub.get('lan_doc', '未知语言')}: ID={sub.get('id')}")

            return True
        else:
            print("\n⚠️  即使使用Cookies,该视频仍没有可提取的字幕")
            print("   这说明字幕可能是硬字幕(烧录在画面上)")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def create_cookies_template():
    """创建cookies模板文件"""
    template = {
        "SESSDATA": "你的SESSDATA值",
        "bili_jct": "你的bili_jct值",
        "DedeUserID": "你的DedeUserID值",
        "DedeUserID__ckMd5": "你的DedeUserID__ckMd5值",
        "buvid3": "可选:浏览器标识"
    }

    with open("cookies_template.json", 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)

    print("✓ 已创建 cookies_template.json 模板文件")
    print("  请编辑该文件并填入你的真实Cookie值")


def main():
    print(INSTRUCTIONS)

    bvid = "BV1Hwi4BYEJz"

    # 尝试从文件加载cookies
    print("\n正在尝试加载Cookies...")
    cookies = load_cookies_from_file("cookies.json")

    if not cookies:
        # 尝试从文本文件加载
        try:
            with open("cookies.txt", 'r', encoding='utf-8') as f:
                cookie_string = f.read().strip()
            cookies = load_cookies_from_string(cookie_string)
            print("✓ 从 cookies.txt 加载Cookies成功")
        except:
            print("\n未找到Cookies文件")
            print("创建模板文件方便你填写...")
            create_cookies_template()
            print("\n请按照上面的说明获取B站Cookies!")
            return

    # 显示加载的cookies(隐藏敏感信息)
    print("\n已加载的Cookies:")
    for key in cookies:
        value = cookies[key]
        if len(value) > 10:
            display_value = value[:5] + "***" + value[-3:]
        else:
            display_value = "***"
        print(f"  {key}: {display_value}")

    # 检查必需的cookies
    required = ['SESSDATA', 'bili_jct']
    missing = [k for k in required if k not in cookies]

    if missing:
        print(f"\n⚠️  缺少必需的Cookies: {', '.join(missing)}")
        print("   某些功能可能无法使用")

    # 测试字幕提取
    print("\n开始测试字幕提取...")
    print("=" * 80)
    success = test_subtitle_with_cookies(bvid, cookies)
    print("=" * 80)

    if success:
        print("\n✅ Cookies配置成功!")
        print("   你可以使用这些Cookies来提取字幕了")
        print("\n下一步:")
        print("1. 将cookies.json文件保存好")
        print("2. 运行主程序提取字幕")
    else:
        print("\n❌ 无法提取字幕")
        print("   可能原因:")
        print("   - 该视频确实没有可提取的字幕(可能是硬字幕)")
        print("   - Cookies已过期,请重新获取")
        print("   - 需要更完整的Cookies信息")


if __name__ == "__main__":
    main()
