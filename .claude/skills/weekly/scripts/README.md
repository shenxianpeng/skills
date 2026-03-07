# Scripts 脚本工具

这个目录包含用于生成周刊的辅助脚本。

## 📋 脚本列表

### 1. image_extractor.py - 智能图片提取器 ⭐ 新增

**用途**：从网页和 GitHub 项目中智能提取图片

**核心功能**：
- 从文章页面提取 og:image、twitter:image
- 提取文章首图（自动过滤装饰性图片）
- 从 GitHub README 提取项目图片
- 获取 GitHub Social Preview 图

**依赖**：
```bash
pip install -r skills/weekly/scripts/requirements.txt
```

**用法**：
```bash
python skills/weekly/scripts/image_extractor.py <url>
```

**示例**：
```bash
# 从博客文章提取图片
python skills/weekly/scripts/image_extractor.py \
    https://netflixtechblog.com/article-title

# 从 GitHub 项目提取图片
python skills/weekly/scripts/image_extractor.py \
    https://github.com/microsoft/vscode
```

**提取优先级**：
1. ✅ og:image / twitter:image meta 标签
2. ✅ 文章内容中的第一张大图（宽度 ≥ 400px）
3. ✅ GitHub Social Preview / README 图片
4. ⏬ 如果都没有，需要手动搜索

---

### 2. download_image.py - 下载单张图片

**用途**：从 URL 下载单张图片到指定路径

**依赖**：
```bash
pip install -r skills/weekly/scripts/requirements.txt
```

**用法**：
```bash
python skills/weekly/scripts/download_image.py <image_url> <output_path>
```

**示例**：
```bash
# 下载封面图
python skills/weekly/scripts/download_image.py \
    https://unsplash.com/photos/example.jpg \
    output/weekly/2026/weekly-3/featured.png

# 下载新闻图片
python skills/weekly/scripts/download_image.py \
    https://example.com/news.png \
    output/weekly/2026/weekly-3/news-1.png
```

**特性**：
- ✅ 自动创建输出目录
- ✅ 模拟浏览器请求头
- ✅ 自动检测图片格式
- ✅ 显示下载进度和文件大小
- ✅ 支持超时设置（30秒）

---

### 3. download_weekly_images.py - 智能批量下载周刊图片 ⭐ 升级

**用途**：根据 JSON 配置文件智能下载周刊所有图片

**新特性 v2.0**：
- ✅ **智能提取**：自动从文章 URL 提取图片
- ✅ **GitHub 支持**：自动获取 GitHub 项目图片
- ✅ **降级机制**：提取失败时使用备用 URL
- ✅ **详细报告**：显示每张图片的来源和状态

**依赖**：
```bash
pip install -r skills/weekly/scripts/requirements.txt
```

**用法**：
```bash
python skills/weekly/scripts/download_weekly_images.py <year> <week_number> <config_json>
```

**示例**：
```bash
python skills/weekly/scripts/download_weekly_images.py 2026 3 images.json
```

**JSON 配置格式（智能模式）** ⭐ 推荐：

创建 `images.json` 文件：
```json
{
    "featured": {
        "url": "https://example.com/trending-article",
        "title": "Article Title",
        "type": "article"
    },
    "news": [
        {
            "url": "https://aws.amazon.com/blogs/devops/new-feature",
            "title": "AWS DevOps 新功能",
            "type": "article"
        },
        {
            "url": "https://kubernetes.io/blog/2026/announcement",
            "title": "Kubernetes 1.30 发布",
            "type": "article",
            "fallback_url": "https://images.unsplash.com/photo-xxx"
        }
    ],
    "blog": [
        {
            "url": "https://netflixtechblog.com/microservices-architecture",
            "title": "Microservices at Scale",
            "type": "article"
        }
    ],
    "opensource": [
        {
            "url": "https://github.com/microsoft/vscode",
            "title": "Visual Studio Code",
            "type": "github"
        },
        {
            "url": "https://github.com/kubernetes/kubernetes",
            "title": "Kubernetes",
            "type": "github"
        }
    ],
    "tool": [
        {
            "url": "https://github.com/aidenybai/million",
            "title": "Million.js",
            "type": "github"
        }
    ],
    "ai": [
        {
            "url": "https://github.com/openai/whisper",
            "title": "Whisper",
            "type": "github"
        }
    ],
    "resource": [
        {
            "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
            "title": "MDN JavaScript Guide",
            "type": "article"
        }
    ]
}
```

**传统格式（直接模式）** - 仍然支持：

```json
{
    "featured": "https://unsplash.com/photos/cover.jpg",
    "news": [
        "https://example.com/news1.png",
        "https://example.com/news2.jpg"
    ],
    "blog": [
        "https://example.com/blog1.jpg",
        "https://example.com/blog2.png"
    ],
    "opensource": [
        "https://opengraph.githubassets.com/xxx/owner/repo"
    ],
    "tool": [
        "https://example.com/tool1.png"
    ],
    "ai": [
        "https://example.com/ai1.png",
        "https://example.com/ai2.jpg"
    ],
    "resource": [
        "https://example.com/resource1.jpg"
    ]
}
```

---

## 🚀 快速开始

### 安装依赖

```bash
cd /Users/sxp/Repos/shenxianpeng/skills
pip install -r skills/weekly/scripts/requirements.txt
```

### 工作流示例

#### 方式 1：智能模式（推荐）⭐

**步骤 1**：测试单个 URL 的图片提取

```bash
# 测试博客文章
python skills/weekly/scripts/image_extractor.py \
    https://netflixtechblog.com/microservices-at-scale

# 测试 GitHub 项目
python skills/weekly/scripts/image_extractor.py \
    https://github.com/microsoft/vscode
```

**步骤 2**：创建智能配置 `images.json`

```json
{
    "featured": {
        "url": "https://example.com/trending-tech-2026",
        "title": "2026 技术趋势",
        "type": "article"
    },
    "news": [
        {
            "url": "https://aws.amazon.com/blogs/devops/new-features",
            "title": "AWS DevOps 新功能",
            "type": "article"
        }
    ],
    "opensource": [
        {
            "url": "https://github.com/kubernetes/kubernetes",
            "title": "Kubernetes",
            "type": "github"
        }
    ]
}
```

**步骤 3**：执行智能批量下载

```bash
python skills/weekly/scripts/download_weekly_images.py 2026 3 images.json
```

**输出示例**：
```
📁 输出目录: output/weekly/2026/weekly-3
🚀 开始智能下载图片...
============================================================

📷 封面图:
  🔍 正在分析页面: https://example.com/trending-tech-2026
  ✅ 找到 og:image
正在下载: https://example.com/images/cover.jpg
✅ 下载成功: output/weekly/2026/weekly-3/featured.jpg (245678 bytes)

📌 行业动态:
  [1] AWS DevOps 新功能
  🔍 正在分析页面: https://aws.amazon.com/blogs/devops/new-features
  ✅ 找到 og:image
正在下载: https://aws-blog.com/images/feature.png
✅ 下载成功: output/weekly/2026/weekly-3/news-1.png (123456 bytes)

📌 开源推荐:
  [1] Kubernetes
  🔍 正在获取 GitHub 项目图片: kubernetes/kubernetes
  ✅ 找到 GitHub Social Preview
正在下载: https://opengraph.githubassets.com/xxx/kubernetes/kubernetes
✅ 下载成功: output/weekly/2026/weekly-3/opensource-1.png (345678 bytes)

============================================================
📊 下载总结:
  ✅ 成功: 3/3 张
  ❌ 失败: 0/3 张
  📁 位置: output/weekly/2026/weekly-3
============================================================
```

#### 方式 2：混合模式（智能+降级）

为不稳定的网站添加降级 URL：

```json
{
    "news": [
        {
            "url": "https://example.com/article",
            "title": "Article Title",
            "type": "article",
            "fallback_url": "https://images.unsplash.com/photo-xxx"
        }
    ]
}
```

如果智能提取失败，会自动使用 `fallback_url`。

#### 方式 3：传统模式（直接 URL）

仍然支持直接图片 URL：

```json
{
    "featured": "https://images.unsplash.com/photo-cover",
    "news": [
        "https://example.com/news1.png",
        "https://example.com/news2.jpg"
    ]
}
```

```bash
python skills/weekly/scripts/download_weekly_images.py 2026 3 images.json
```

**输出示例**：
```
📁 输出目录: output/weekly/2026/weekly-3
开始下载图片...

正在下载: https://images.unsplash.com/photo-cover
✅ 下载成功: output/weekly/2026/weekly-3/featured.jpg (245678 bytes)

📌 行业动态:
正在下载: https://aws.amazon.com/blogs/news1.png
✅ 下载成功: output/weekly/2026/weekly-3/news-1.png (123456 bytes)

正在下载: https://kubernetes.io/blog/news2.jpg
✅ 下载成功: output/weekly/2026/weekly-3/news-2.jpg (234567 bytes)

============================================================
✅ 下载完成: 5/5 张图片成功
📁 保存位置: output/weekly/2026/weekly-3
```

---

## 📝 图片来源建议

### 1. 官方来源（优先）

```bash
# GitHub 项目 Social Preview
https://opengraph.githubassets.com/{hash}/{owner}/{repo}

# 官方网站 logo
https://kubernetes.io/images/kubernetes-horizontal-color.png
https://www.docker.com/wp-content/uploads/2022/03/Moby-logo.png
```

### 2. 免费图库

- **Unsplash**: https://unsplash.com/
- **Pexels**: https://www.pexels.com/

### 3. 技术博客配图

- AWS Blog
- Google Cloud Blog
- Netflix TechBlog
- Dev.to
- Medium

---

## 🛠️ 高级用法

### 自定义请求头

编辑 `download_image.py` 中的 `headers` 字典：

```python
headers = {
    'User-Agent': 'Your Custom User Agent',
    'Referer': 'https://example.com'
}
```

### 修改超时时间

```python
response = requests.get(url, headers=headers, timeout=60, stream=True)  # 60秒超时
```

### 支持代理

```python
proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080'
}
response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
```

---

## ⚠️ 注意事项

1. **版权问题**：确保下载的图片有合法使用权限
2. **网络问题**：某些网站可能需要代理或特殊处理
3. **图片格式**：脚本会自动检测并使用正确的扩展名
4. **错误处理**：下载失败会显示错误信息但不会中断整个流程
5. **文件覆盖**：重复下载会覆盖现有文件

---

## 🔧 故障排除

### requests 模块未安装

```bash
pip install -r skills/weekly/scripts/requirements.txt
```

### 下载失败（403/404）

- 检查 URL 是否正确
- 某些网站可能需要特定的 User-Agent 或 Referer
- 尝试在浏览器中访问 URL 验证

### 超时错误

- 增加超时时间
- 检查网络连接
- 尝试使用代理

### 权限错误

```bash
chmod +x skills/weekly/scripts/download_image.py
chmod +x skills/weekly/scripts/download_weekly_images.py
```

---

## 📚 相关文档

- 周刊 Skills: [../SKILL.md](../SKILL.md)
- 项目说明: [../../README.md](../../README.md)
- 图片下载 Skill: [../download_images.md](../download_images.md)
