# Scripts 脚本工具

这个目录包含用于生成周刊的辅助脚本。

## 📋 脚本列表

### 1. download_image.py - 下载单张图片

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

### 2. download_weekly_images.py - 批量下载周刊图片

**用途**：根据 JSON 配置文件批量下载周刊所有图片

**依赖**：
```bash
pip install -r skills/weekly/scripts/requirements.txt
```

**用法**：
```bash
python skills/weekly/scripts/download_weekly_images.py <year> <week_number> <images_json>
```

**示例**：
```bash
python skills/weekly/scripts/download_weekly_images.py 2026 3 images.json
```

**JSON 配置格式**：

创建 `images.json` 文件：
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

**输出结构**：
```
output/weekly/2026/weekly-3/
├── featured.jpg       # 封面图
├── news-1.png         # 行业动态图片
├── news-2.jpg
├── blog-1.jpg         # 深度阅读图片
├── blog-2.png
├── tool-1.png         # 效率工具图片
├── ai-1.png           # AI 项目图片
├── ai-2.jpg
└── resource-1.jpg     # 学习资源图片
```

**特性**：
- ✅ 批量下载多张图片
- ✅ 按章节自动命名
- ✅ 自动创建目录结构
- ✅ 显示下载统计信息
- ✅ 支持 JSON 配置

---

## 🚀 快速开始

### 安装依赖

```bash
pip install -r skills/weekly/scripts/requirements.txt
```

### 示例工作流

#### 1. 下载单张图片

```bash
# 下载 Unsplash 封面图
python skills/weekly/scripts/download_image.py \
    https://images.unsplash.com/photo-example \
    output/weekly/2026/weekly-3/featured.png
```

#### 2. 批量下载周刊图片

**步骤 1**：创建 `images.json` 配置文件

```json
{
    "featured": "https://images.unsplash.com/photo-cover",
    "news": [
        "https://aws.amazon.com/blogs/news1.png",
        "https://kubernetes.io/blog/news2.jpg"
    ],
    "blog": [
        "https://netflixtechblog.com/article1.jpg"
    ],
    "tool": [
        "https://github.com/user/repo/logo.png"
    ],
    "ai": [
        "https://github.com/ai-project/screenshot.png"
    ]
}
```

**步骤 2**：执行批量下载

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
