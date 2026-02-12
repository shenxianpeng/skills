#!/usr/bin/env python3
"""
智能批量下载周刊图片的脚本

支持两种模式：
1. 智能模式：从文章 URL 自动提取图片
2. 直接模式：从图片 URL 直接下载

用法：
    python scripts/download_weekly_images.py <year> <week_number> <config_json>
    
示例：
    python scripts/download_weekly_images.py 2026 3 images.json
    
images.json 格式（智能模式）：
{
    "featured": {
        "url": "https://example.com/article",
        "title": "Article Title",
        "type": "article"
    },
    "news": [
        {
            "url": "https://example.com/news-article",
            "title": "News Title",
            "type": "article"
        }
    ],
    "opensource": [
        {
            "url": "https://github.com/owner/repo",
            "title": "Project Name",
            "type": "github"
        }
    ]
}

或简化格式（直接模式）：
{
    "featured": "https://example.com/cover.png",
    "news": ["https://example.com/news1.png"]
}
"""

import sys
import json
import os
import re
from pathlib import Path
from download_image import download_image, get_image_extension
from image_extractor import ImageExtractor


def get_image_url_from_config(config_item, extractor):
    """
    从配置项获取图片 URL（支持智能提取）
    
    Args:
        config_item: 配置项（字符串或字典）
        extractor: ImageExtractor 实例
    
    Returns:
        图片 URL 或 None
    """
    # 如果是字符串，直接返回（假设是图片 URL）
    if isinstance(config_item, str):
        return config_item
    
    # 如果是字典，进行智能提取
    if isinstance(config_item, dict):
        url = config_item.get('url')
        title = config_item.get('title', '')
        content_type = config_item.get('type', 'article')
        
        if not url:
            return None
        
        # 判断是否为 GitHub URL
        if content_type == 'github' or 'github.com' in url:
            match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
            if match:
                owner, repo = match.groups()
                # 移除可能的 .git 后缀
                repo = repo.replace('.git', '').split('/')[0]
                result = extractor.extract_from_github(owner, repo)
                if result:
                    return result['url']
        else:
            # 尝试从文章页面提取
            result = extractor.extract_from_url(url, title)
            if result:
                return result['url']
        
        # 如果智能提取失败，检查是否有降级的图片 URL
        if 'fallback_url' in config_item:
            print(f"  ⚠️  使用降级 URL")
            return config_item['fallback_url']
        
        # 如果没有降级，尝试根据关键词搜索
        print(f"  ⚠️  智能提取失败，需要手动指定图片 URL 或使用搜索")
        return None
    
    return None


def download_weekly_images(year, week_number, images_config):
    """
    批量下载周刊图片（支持智能提取）
    
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
    
    # 初始化图片提取器
    extractor = ImageExtractor()
    
    success_count = 0
    total_count = 0
    failed_items = []
    
    print(f"📁 输出目录: {output_dir}")
    print(f"🚀 开始智能下载图片...\n")
    print(f"{'='*60}\n")
    
    # 下载封面图
    if 'featured' in images_config:
        print(f"📷 封面图:")
        total_count += 1
        
        image_url = get_image_url_from_config(images_config['featured'], extractor)
        
        if image_url:
            ext = get_image_extension(image_url)
            output_path = output_dir / f"featured{ext}"
            if download_image(image_url, str(output_path)):
                success_count += 1
            else:
                failed_items.append(('featured', 'featured'))
        else:
            print(f"  ❌ 无法获取图片 URL")
            failed_items.append(('featured', 'featured'))
        
        print()
    
    # 下载各章节图片
    sections = {
        'news': '行业动态',
        'blog': '深度阅读',
        'opensource': '开源推荐',
        'tool': '效率工具',
        'ai': 'AI 相关',
        'resource': '学习资源'
    }
    
    for section_key, section_name in sections.items():
        if section_key in images_config:
            items = images_config[section_key]
            if isinstance(items, str) or isinstance(items, dict):
                items = [items]
            
            print(f"📌 {section_name}:")
            for i, item in enumerate(items, 1):
                total_count += 1
                
                # 如果是字典，显示标题
                item_title = ''
                if isinstance(item, dict):
                    item_title = item.get('title', f'{section_name} {i}')
                    print(f"  [{i}] {item_title}")
                else:
                    print(f"  [{i}] {section_name} {i}")
                
                image_url = get_image_url_from_config(item, extractor)
                
                if image_url:
                    ext = get_image_extension(image_url)
                    output_path = output_dir / f"{section_key}-{i}{ext}"
                    if download_image(image_url, str(output_path)):
                        success_count += 1
                    else:
                        failed_items.append((section_name, item_title or f'{section_name} {i}'))
                else:
                    print(f"  ❌ 无法获取图片 URL")
                    failed_items.append((section_name, item_title or f'{section_name} {i}'))
                
                print()
            
            print()
    
    # 输出总结
    print(f"{'='*60}")
    print(f"📊 下载总结:")
    print(f"  ✅ 成功: {success_count}/{total_count} 张")
    print(f"  ❌ 失败: {len(failed_items)}/{total_count} 张")
    print(f"  📁 位置: {output_dir}")
    
    if failed_items:
        print(f"\n⚠️  失败的项目:")
        for section, title in failed_items:
            print(f"  - [{section}] {title}")
        print(f"\n💡 建议:")
        print(f"  1. 检查配置文件中的 URL 是否正确")
        print(f"  2. 为失败的项目添加 fallback_url")
        print(f"  3. 或使用 Unsplash 搜索关键词")
    
    print(f"{'='*60}\n")
    
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
