#!/usr/bin/env python3
"""
批量下载周刊图片的脚本

从 JSON 配置文件读取图片 URL 列表，批量下载到周刊目录

用法：
    python scripts/download_weekly_images.py <year> <week_number> <images_json>
    
示例：
    python scripts/download_weekly_images.py 2026 3 images.json
    
images.json 格式：
{
    "featured": "https://example.com/cover.png",
    "news": [
        "https://example.com/news1.png",
        "https://example.com/news2.jpg"
    ],
    "blog": [
        "https://example.com/blog1.jpg"
    ],
    "tool": [
        "https://example.com/tool1.png"
    ],
    "ai": [
        "https://example.com/ai1.png"
    ]
}
"""

import sys
import json
import os
from pathlib import Path
from download_image import download_image, get_image_extension


def download_weekly_images(year, week_number, images_config):
    """
    批量下载周刊图片
    
    Args:
        year: 年份
        week_number: 期数
        images_config: 图片配置字典
    
    Returns:
        成功下载的图片数量
    """
    # 确定输出目录
    output_dir = Path(f"output/weekly/{year}/weekly-{week_number}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    total_count = 0
    
    print(f"📁 输出目录: {output_dir}")
    print(f"开始下载图片...\n")
    
    # 下载封面图
    if 'featured' in images_config:
        total_count += 1
        url = images_config['featured']
        ext = get_image_extension(url)
        output_path = output_dir / f"featured{ext}"
        if download_image(url, str(output_path)):
            success_count += 1
        print()
    
    # 下载各章节图片
    sections = {
        'news': '行业动态',
        'blog': '深度阅读',
        'tool': '效率工具',
        'ai': 'AI 相关',
        'resource': '学习资源'
    }
    
    for section_key, section_name in sections.items():
        if section_key in images_config:
            urls = images_config[section_key]
            if isinstance(urls, str):
                urls = [urls]
            
            print(f"📌 {section_name}:")
            for i, url in enumerate(urls, 1):
                total_count += 1
                ext = get_image_extension(url)
                output_path = output_dir / f"{section_key}-{i}{ext}"
                if download_image(url, str(output_path)):
                    success_count += 1
            print()
    
    print(f"{'='*60}")
    print(f"✅ 下载完成: {success_count}/{total_count} 张图片成功")
    print(f"📁 保存位置: {output_dir}")
    
    return success_count


def main():
    if len(sys.argv) < 4:
        print("用法: python scripts/download_weekly_images.py <year> <week_number> <images_json>")
        print("\n示例:")
        print("  python scripts/download_weekly_images.py 2026 3 images.json")
        sys.exit(1)
    
    year = sys.argv[1]
    week_number = sys.argv[2]
    json_file = sys.argv[3]
    
    # 读取 JSON 配置
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            images_config = json.load(f)
    except FileNotFoundError:
        print(f"❌ 文件不存在: {json_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式错误: {e}")
        sys.exit(1)
    
    success_count = download_weekly_images(year, week_number, images_config)
    sys.exit(0 if success_count > 0 else 1)


if __name__ == '__main__':
    main()
