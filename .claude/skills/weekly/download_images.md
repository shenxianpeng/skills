---
name: download-images
description: Intelligently downloads and manages images for weekly newsletter by extracting from article pages first, then falling back to search if needed. Prioritizes article featured images, OpenGraph images, and relevant illustrations before using generic stock photos.
metadata:
  author: shenxianpeng
  version: "2.0"
---

# 智能下载和管理周刊图片

为周刊的各个章节智能下载和管理相关图片。优先从文章页面提取图片，如果文章没有合适图片，再根据文章主题搜索相关图片。

## 输入
- `weekly_path`: 周刊目录路径（如 `output/weekly/2026/weekly-3/`）
- `content_sections`: 周刊内容的各个章节及其关键词

## 过程

### 步骤 1：确定图片需求

为以下章节准备图片（**不包括"行业观点"**）：

1. **本周封面** - 1张主题图片
2. **行业动态** - 每条新闻 1 张相关图片
3. **深度阅读** - 每篇文章 1 张相关图片
4. **效率工具** - 每个工具的 logo 或截图
5. **AI 相关** - 每个项目的 logo 或架构图
6. **学习资源** - 每个资源的封面图或相关图片
7. **精彩摘要** - 可选，视情况添加

### 步骤 2：智能图片获取策略 ⭐

**核心原则：优先使用文章自带图片，没有再搜索相关图片**

#### 对于文章类内容（新闻、博客、资源）

**优先级顺序：**

1. **文章页面提取**（最优先） ⭐
   - 提取 OpenGraph 图片：
     - `<meta property="og:image" content="...">`
     - `<meta name="twitter:image" content="...">`
   - 提取文章第一张高质量图片：
     - 文章 body 中的第一张图片（宽度 > 400px）
     - 排除 logo、icon、广告等小图片
   - 提取文章封面图（如果有明确的 featured image）

2. **作者/出版物 logo**（次优先）
   - 官方网站 logo
   - 博客平台标识
   - 媒体品牌图

3. **关键词搜索图片**（降级方案）
   - 从文章标题/内容提取关键词
   - Unsplash 主题搜索：`https://source.unsplash.com/800x450/?{keywords}`
   - Pexels API 搜索

#### 对于 GitHub 项目（工具、开源项目、AI 项目）

**优先级顺序：**

1. **GitHub 官方图片**（最优先）
   - GitHub Social Preview：`https://opengraph.githubassets.com/{hash}/{owner}/{repo}`
   - README 中的 logo/banner 图片
   - 项目文档中的架构图

2. **项目官网图片**（次优先）
   - 官方网站的 logo
   - 产品截图
   - Demo 图片

3. **项目主题搜索**（降级方案）
   - 根据项目类型和技术栈搜索相关图片
   - 例如：AI 工具 → 搜索 "artificial intelligence"
   - 例如：DevOps 工具 → 搜索 "devops automation"

#### 提取示例代码逻辑

```python
def get_image_for_article(url, title, content_type):
    """
    智能获取文章图片
    
    Args:
        url: 文章 URL
        title: 文章标题
        content_type: 内容类型 (news/blog/resource)
    
    Returns:
        图片 URL 和来源说明
    """
    # 1. 尝试从文章页面提取
    image_url = extract_og_image(url)
    if image_url:
        return (image_url, "og:image from article")
    
    image_url = extract_first_article_image(url)
    if image_url:
        return (image_url, "article content image")
    
    # 2. 尝试获取媒体 logo
    image_url = get_publication_logo(url)
    if image_url:
        return (image_url, "publication logo")
    
    # 3. 根据文章主题搜索
    keywords = extract_keywords(title)
    image_url = search_unsplash(keywords)
    return (image_url, f"unsplash search: {keywords}")

def get_image_for_github(owner, repo, project_type):
    """
    获取 GitHub 项目图片
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        project_type: 项目类型 (tool/opensource/ai)
    
    Returns:
        图片 URL 和来源说明
    """
    # 1. GitHub Social Preview
    image_url = get_github_social_preview(owner, repo)
    if validate_image(image_url):
        return (image_url, "GitHub social preview")
    
    # 2. README 中的图片
    image_url = extract_readme_image(owner, repo)
    if image_url:
        return (image_url, "README image")
    
    # 3. 项目官网
    website = get_project_website(owner, repo)
    if website:
        image_url = extract_og_image(website)
        if image_url:
            return (image_url, "project website")
    
    # 4. 根据项目类型搜索
    keywords = f"{repo} {project_type}"
    image_url = search_unsplash(keywords)
    return (image_url, f"unsplash search: {keywords}")
```

### 步骤 2.5：图片质量验证

对提取的图片进行验证：

1. **可访问性检查**：HTTP 200 状态
2. **尺寸验证**：宽度 ≥ 400px，高度 ≥ 300px
3. **格式检查**：支持 JPG、PNG、WebP
4. **内容相关性**：避免无关或低质量图片

如果图片不符合要求，自动降级到下一优先级。

### 步骤 3：创建图片配置和下载

#### 3.1 创建 images.json 配置文件

在周刊目录下创建 `images.json`，记录所有图片来源：

```json
{
  "featured": {
    "url": "https://images.unsplash.com/photo-xxx",
    "source": "unsplash",
    "keywords": "technology network"
  },
  "news": [
    {
      "url": "https://example.com/article-image.jpg",
      "source": "og:image from article",
      "title": "AWS 发布新功能"
    },
    {
      "url": "https://source.unsplash.com/800x450/?devops",
      "source": "unsplash search: devops",
      "title": "GitHub Actions 更新"
    }
  ],
  "blog": [
    {
      "url": "https://blog.example.com/featured.png",
      "source": "article featured image",
      "title": "Why Service Mesh Failed"
    }
  ],
  "opensource": [
    {
      "url": "https://opengraph.githubassets.com/xxx/owner/repo",
      "source": "GitHub social preview",
      "title": "AionUi"
    }
  ],
  "ai": [...],
  "resource": [...]
}
```

#### 3.2 运行下载脚本

使用增强的 Python 脚本下载所有图片：

```bash
cd /Users/sxp/Repos/shenxianpeng/skills
python3 skills/weekly/scripts/download_weekly_images.py 2026 3 output/weekly/2026/weekly-3/images.json
```

脚本功能：
- 读取 images.json 配置
- 智能下载每张图片
- 自动重试失败的下载
- 验证图片尺寸和格式
- 生成下载报告

### 步骤 4：更新 Markdown 引用

在 markdown 中使用**相对路径**引用图片：

```markdown
## 本周封面

![本周封面](featured.png)

简单的解决方案往往比复杂的架构更稳定。（[via Unsplash](原始URL)）

## 行业动态

1、[AWS 发布 DevOps Agent](链接)

![AWS DevOps Agent](news-1.png)

AWS 在 re:Invent 2025 上发布了 DevOps Agent...

## 深度阅读

1、[Why Service Mesh Never Took Off](链接)（英文）

![Service Mesh](blog-1.jpg)

这篇文章分析了为什么 Service Mesh 技术...

## 效率工具

1、[AionUi](https://github.com/iOfficeAI/AionUi)

![AionUi Logo](tool-1.png)

一个免费、本地、开源的 AI 编程助手 UI...

## AI 相关

1、[LEANN](https://github.com/yichuan-w/LEANN)

![LEANN Architecture](ai-1.png)

在个人设备上运行快速、准确且 100% 私密的 RAG 应用...
```

## 图片选择建议（按内容类型）

### 行业动态（News）
**优先级：**
1. ✅ 新闻文章的 og:image 或 featured image
2. ✅ 新闻文章中的第一张配图（产品截图、发布会图等）
3. ✅ 公司/产品 logo
4. ⏬ 根据新闻关键词搜索 Unsplash（如："AWS cloud", "GitHub copilot"）

**避免：** 不要使用与新闻无关的通用科技图片

### 深度阅读（Blog）
**优先级：**
1. ✅ 博客文章的 og:image 或封面图
2. ✅ 文章中的架构图、流程图、示意图
3. ✅ 文章首图（如果是相关技术内容）
4. ⏬ 根据文章主题搜索（如："microservices architecture", "kubernetes deployment"）

**避免：** 不要使用装饰性图片，要选择能体现文章技术内容的图片

### 开源推荐（Opensource）
**优先级：**
1. ✅ GitHub Social Preview 图（自动生成的项目卡片）
2. ✅ README 中的 logo/banner
3. ✅ 项目官网的产品截图
4. ✅ 项目文档中的效果展示图
5. ⏬ 根据项目类型搜索（如："code editor", "terminal app"）

**避免：** 不要使用与项目功能无关的图片

### 效率工具（Tool）
**同开源推荐**，优先项目实际截图和 logo

### AI 相关（AI）
**优先级：**
1. ✅ 项目的架构图、技术示意图
2. ✅ AI 产品的效果展示图
3. ✅ 官方博客文章的配图
4. ⏬ 根据 AI 应用类型搜索（如："machine learning", "neural network"）

### 学习资源（Resource）
**优先级：**
1. ✅ 课程/教程的封面图
2. ✅ 书籍封面
3. ✅ 教程网站的 og:image
4. ⏬ 根据学习主题搜索（如："programming tutorial", "database design"）

## 图片规范

### 尺寸
- **封面图**：建议 1200x630px（适合社交分享）
- **章节图片**：建议 800x450px 或 16:9 比例
- **Logo/图标**：建议 400x400px 或原始尺寸

### 格式
- 优先使用 **JPG**（照片）或 **PNG**（logo、截图）
- WebP 格式可选（更小的文件大小）
- 避免使用 GIF（除非必要的动画）

### 文件命名
```
featured.png          # 封面图（固定名称，Hugo 自动识别）
news-{n}.{ext}        # 行业动态第 n 条
blog-{n}.{ext}        # 深度阅读第 n 篇
tool-{n}.{ext}        # 效率工具第 n 个
ai-{n}.{ext}          # AI 相关第 n 个
resource-{n}.{ext}    # 学习资源第 n 个
quote-{n}.{ext}       # 精彩摘要第 n 个（可选）
```

## 版权和归属

### 必须包含的信息
- Unsplash/Pexels 图片：在图片说明中添加 `(via Unsplash/Pexels)`
- 官方图片：在图片说明中标注来源
- GitHub 项目：可以使用项目中的图片（遵循项目许可证）

### 示例
```markdown
![](featured.png)
DevOps 工程师在工作。（[via Unsplash](https://unsplash.com/photos/xxx)）

![](tool-1.png)
AionUi 界面截图。（[via GitHub](https://github.com/iOfficeAI/AionUi)）
```

## 输出

图片文件保存在周刊目录中：
- 路径：`content/posts/{YEAR}/weekly-{week_number}/`
- 每个章节的内容都应该包含：
  1. 相关的图片文件（保存在周刊目录）
  2. Markdown 中的图片引用（使用相对路径，如 `![](featured.png)`）
  3. 图片来源说明

## 注意事项

- ❌ **不要为"行业观点"章节添加图片**
- ✅ **必须先尝试从文章页面提取图片** ⭐ - 这是最重要的原则
- ✅ 优先使用文章自带的 og:image 和 featured image
- ✅ 对于 GitHub 项目，优先使用 Social Preview 和 README 图片
- ✅ 只有在文章没有合适图片时，才根据关键词搜索
- ✅ 确保图片文件名简洁且有意义
- ✅ 保持图片质量，避免模糊或低分辨率（宽度 ≥ 400px）
- ✅ 图片必须与内容高度相关，不要随意配图
- ✅ 验证图片可访问性，避免失效链接
- ⚠️ 如果找不到合适的图片，宁可不配图也不要强行配不相关的图片

## 图片提取优势

使用这种智能提取策略的好处：

1. **内容相关性更强**：使用文章原图，图片内容与文章主题完全匹配
2. **视觉连贯性好**：读者点击链接后看到的内容与图片一致，不会产生误导
3. **节省时间**：自动提取，无需手动搜索和筛选
4. **版权清晰**：使用文章官方图片，版权归属明确
5. **提升阅读体验**：相关图片能帮助读者快速理解内容重点
