#!/usr/bin/env python3
"""
下载图片到周刊目录的脚本

用法：
    python scripts/download_image.py <image_url> <output_path>
    
示例：
    python scripts/download_image.py https://example.com/image.png output/weekly/2026/weekly-3/featured.png
"""

import sys
import os
import requests
from pathlib import Path
from urllib.parse import urlparse


def download_image(url, output_path):
    """
    从 URL 下载图片到指定路径
    
    Args:
        url: 图片 URL
        output_path: 输出文件路径
    """
    try:
        # 创建输出目录
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 设置请求头，模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        print(f"正在下载: {url}")
        
        # 下载图片
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # 保存图片
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size = output_file.stat().st_size
        print(f"✅ 下载成功: {output_path} ({file_size} bytes)")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 下载失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False


def get_image_extension(url, response=None):
    """
    从 URL 或响应中获取图片扩展名
    
    Args:
        url: 图片 URL
        response: HTTP 响应对象（可选）
    
    Returns:
        图片扩展名，如 '.png', '.jpg'
    """
    # 首先尝试从 URL 中获取
    parsed_url = urlparse(url)
    path = parsed_url.path
    if '.' in path:
        ext = os.path.splitext(path)[1]
        if ext.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']:
            return ext.lower()
    
    # 如果提供了响应，从 Content-Type 中获取
    if response:
        content_type = response.headers.get('Content-Type', '')
        if 'image/png' in content_type:
            return '.png'
        elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
            return '.jpg'
        elif 'image/gif' in content_type:
            return '.gif'
        elif 'image/webp' in content_type:
            return '.webp'
        elif 'image/svg+xml' in content_type:
            return '.svg'
    
    # 默认返回 .png
    return '.png'


def main():
    if len(sys.argv) < 3:
        print("用法: python scripts/download_image.py <image_url> <output_path>")
        print("\n示例:")
        print("  python scripts/download_image.py https://example.com/image.png output/weekly/2026/weekly-3/featured.png")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2]
    
    # 如果输出路径没有扩展名，尝试自动添加
    if not os.path.splitext(output_path)[1]:
        ext = get_image_extension(url)
        output_path = output_path + ext
    
    success = download_image(url, output_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
