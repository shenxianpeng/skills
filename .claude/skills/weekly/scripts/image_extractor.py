#!/usr/bin/env python3
"""
智能图片提取模块

从网页中智能提取图片，优先级：
1. OpenGraph 图片 (og:image)
2. Twitter Card 图片 (twitter:image)
3. 文章首图（body 中第一张大图）
4. 降级到关键词搜索
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re


class ImageExtractor:
    """图片提取器"""
    
    def __init__(self, timeout=30):
        """
        初始化提取器
        
        Args:
            timeout: HTTP 请求超时时间（秒）
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def extract_from_url(self, url, title=None):
        """
        从 URL 提取图片
        
        Args:
            url: 网页 URL
            title: 文章标题（可选，用于关键词提取）
        
        Returns:
            字典 {'url': 图片URL, 'source': 来源说明} 或 None
        """
        try:
            print(f"  🔍 正在分析页面: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 1. 尝试提取 og:image
            og_image = self._extract_og_image(soup, url)
            if og_image:
                print(f"  ✅ 找到 og:image")
                return {'url': og_image, 'source': 'og:image from article'}
            
            # 2. 尝试提取 twitter:image
            twitter_image = self._extract_twitter_image(soup, url)
            if twitter_image:
                print(f"  ✅ 找到 twitter:image")
                return {'url': twitter_image, 'source': 'twitter:image from article'}
            
            # 3. 尝试提取文章首图
            article_image = self._extract_article_image(soup, url)
            if article_image:
                print(f"  ✅ 找到文章配图")
                return {'url': article_image, 'source': 'article content image'}
            
            print(f"  ⚠️  未找到文章图片，需要搜索")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  访问失败: {e}")
            return None
        except Exception as e:
            print(f"  ⚠️  提取失败: {e}")
            return None
    
    def _extract_og_image(self, soup, base_url):
        """提取 OpenGraph 图片"""
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            url = og_image['content']
            return self._normalize_url(url, base_url)
        
        # 有些网站使用 name 而不是 property
        og_image = soup.find('meta', attrs={'name': 'og:image'})
        if og_image and og_image.get('content'):
            url = og_image['content']
            return self._normalize_url(url, base_url)
        
        return None
    
    def _extract_twitter_image(self, soup, base_url):
        """提取 Twitter Card 图片"""
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            url = twitter_image['content']
            return self._normalize_url(url, base_url)
        
        twitter_image = soup.find('meta', property='twitter:image')
        if twitter_image and twitter_image.get('content'):
            url = twitter_image['content']
            return self._normalize_url(url, base_url)
        
        return None
    
    def _extract_article_image(self, soup, base_url):
        """
        提取文章中的第一张大图
        
        优先选择：
        1. article 标签内的图片
        2. main 标签内的图片
        3. body 内的图片
        
        过滤条件：
        - 宽度 >= 400px（如果有指定）
        - 排除 logo、icon、avatar 等小图
        """
        # 优先在文章容器中查找
        containers = soup.find_all(['article', 'main', '.post-content', '.article-content'])
        if not containers:
            containers = [soup.body] if soup.body else []
        
        for container in containers:
            images = container.find_all('img')
            
            for img in images:
                # 获取图片 URL
                img_url = img.get('src') or img.get('data-src')
                if not img_url:
                    continue
                
                # 跳过太小的图片（logo、icon 等）
                width = self._get_image_width(img)
                if width and width < 400:
                    continue
                
                # 跳过明显的装饰性图片
                if self._is_decorative_image(img):
                    continue
                
                # 返回第一张符合条件的图片
                return self._normalize_url(img_url, base_url)
        
        return None
    
    def _get_image_width(self, img_tag):
        """获取图片宽度（像素）"""
        width_str = img_tag.get('width')
        if width_str:
            try:
                # 移除 'px' 等单位
                width_str = re.sub(r'[^0-9]', '', str(width_str))
                return int(width_str)
            except ValueError:
                pass
        return None
    
    def _is_decorative_image(self, img_tag):
        """判断是否为装饰性图片"""
        # 检查 class 和 alt 属性
        classes = ' '.join(img_tag.get('class', []))
        alt = img_tag.get('alt', '').lower()
        src = img_tag.get('src', '').lower()
        
        decorative_keywords = [
            'logo', 'icon', 'avatar', 'emoji', 'badge',
            'button', 'social', 'ads', 'banner'
        ]
        
        for keyword in decorative_keywords:
            if keyword in classes.lower() or keyword in alt or keyword in src:
                return True
        
        return False
    
    def _normalize_url(self, url, base_url):
        """
        标准化 URL（处理相对路径）
        
        Args:
            url: 图片 URL（可能是相对路径）
            base_url: 基础 URL
        
        Returns:
            完整的图片 URL
        """
        if not url:
            return None
        
        # 处理协议相对 URL（//example.com/image.jpg）
        if url.startswith('//'):
            parsed_base = urlparse(base_url)
            return f"{parsed_base.scheme}:{url}"
        
        # 处理相对路径
        if not url.startswith(('http://', 'https://')):
            return urljoin(base_url, url)
        
        return url
    
    def extract_from_github(self, owner, repo):
        """
        提取 GitHub 项目图片
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
        
        Returns:
            字典 {'url': 图片URL, 'source': 来源说明} 或 None
        """
        print(f"  🔍 正在获取 GitHub 项目图片: {owner}/{repo}")
        
        # 1. 尝试 GitHub Social Preview
        social_preview_url = f"https://opengraph.githubassets.com/1/{owner}/{repo}"
        if self._validate_image_url(social_preview_url):
            print(f"  ✅ 找到 GitHub Social Preview")
            return {'url': social_preview_url, 'source': 'GitHub social preview'}
        
        # 2. 尝试从 README 提取
        readme_image = self._extract_from_readme(owner, repo)
        if readme_image:
            print(f"  ✅ 找到 README 中的图片")
            return {'url': readme_image, 'source': 'README image'}
        
        print(f"  ⚠️  未找到 GitHub 项目图片")
        return None
    
    def _extract_from_readme(self, owner, repo):
        """从 GitHub README 提取图片"""
        try:
            # 尝试获取 README
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
            response = requests.get(readme_url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code != 200:
                # 尝试 master 分支
                readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
                response = requests.get(readme_url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                content = response.text
                # 查找 markdown 图片语法：![alt](url)
                matches = re.findall(r'!\[.*?\]\((.*?)\)', content)
                if matches:
                    # 返回第一张图片
                    img_url = matches[0]
                    # 如果是相对路径，转换为绝对路径
                    if not img_url.startswith(('http://', 'https://')):
                        img_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{img_url}"
                    return img_url
        
        except Exception as e:
            pass
        
        return None
    
    def _validate_image_url(self, url):
        """验证图片 URL 是否可访问"""
        try:
            response = requests.head(url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def extract_keywords(self, title):
        """
        从标题提取关键词用于搜索
        
        Args:
            title: 文章标题
        
        Returns:
            关键词列表
        """
        if not title:
            return []
        
        # 移除常见的停用词
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # 提取单词
        words = re.findall(r'\b[a-z]+\b', title.lower())
        
        # 过滤停用词和短词
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords[:3]  # 返回前3个关键词


def main():
    """测试函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python image_extractor.py <url>")
        print("示例: python image_extractor.py https://example.com/article")
        sys.exit(1)
    
    url = sys.argv[1]
    
    extractor = ImageExtractor()
    
    # 判断是否为 GitHub URL
    if 'github.com' in url:
        match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if match:
            owner, repo = match.groups()
            result = extractor.extract_from_github(owner, repo)
        else:
            result = extractor.extract_from_url(url)
    else:
        result = extractor.extract_from_url(url)
    
    if result:
        print(f"\n✅ 提取成功:")
        print(f"   URL: {result['url']}")
        print(f"   来源: {result['source']}")
    else:
        print(f"\n❌ 未找到图片")


if __name__ == '__main__':
    main()
