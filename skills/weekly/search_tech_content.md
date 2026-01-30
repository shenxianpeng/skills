---
name: search-tech-content
description: 搜索 DevOps、AI、CI/CD 和 Build 领域的技术内容，包括新闻、博客文章、工具和开源项目。Use when searching for tech news, blog articles, tools, or GitHub projects for weekly newsletter.
---

# 搜索技术内容

搜索 DevOps、AI 工程化、CI/CD 和 Build 领域的最新技术内容，包括博客文章、新闻、开源项目等。

## 输入
- `time_range`: 时间范围（如 "过去7天"、"2026年1月"）
- `content_type`: 内容类型（news/blog/tool/project/resource）
- `keywords`: 搜索关键词（可选）
- `补充模式`: 是否为补充搜索（可选，用于验证失败后的内容补充）
  - 如果是补充模式，自动放宽时间范围和扩展关键词

## 内容数量要求

每个内容类型的最低数量要求：
- **行业动态（news）**：最低 5 条，理想 6-8 条
- **深度阅读（blog）**：最低 3 条，理想 4-5 条  
- **效率工具（tool）**：最低 2 条，理想 3-4 条
- **AI 相关（project）**：最低 2 条，理想 2-3 条
- **学习资源（resource）**：最低 1 条，理想 1-2 条

## 过程

### 1. 确定搜索源和关键词

根据内容类型选择合适的搜索源：

**博客文章（blog）：**
- Medium: `site:medium.com DevOps OR AI [时间]`
- Dev.to: `site:dev.to DevOps OR AI OR open-source [时间]`
- AWS Blog: `site:aws.amazon.com/blogs`
- Google Cloud Blog: `site:cloud.google.com/blog`
- Google AI Blog: `site:ai.googleblog.com`
- Microsoft Blog: `site:devblogs.microsoft.com`
- GitHub Blog: `site:github.blog`
- Meta Engineering: `site:engineering.fb.com`
- Netflix TechBlog: `site:netflixtechblog.com`
- Uber Engineering: `site:eng.uber.com`
- Spotify Engineering: `site:engineering.atspotify.com`
- Linux Foundation: `site:linuxfoundation.org`
- CNCF Blog: `site:cncf.io/blog`
- OpenAI Blog: `site:openai.com/blog`
- Anthropic Blog: `site:anthropic.com/news`

**行业新闻（news）：**
- `DevOps news [时间]`
- `AI engineering news [时间]`
- `Kubernetes updates [时间]`
- `cloud native news [时间]`
- `site:techcrunch.com AI OR DevOps OR open-source`
- `site:infoq.com DevOps OR AI`
- `site:theverge.com tech OR AI`
- `site:arstechnica.com open-source OR tech`
- `Google AI news [时间]`
- `Microsoft GitHub news [时间]`
- `AWS announcements [时间]`
- `Meta open source [时间]`
- `Linux Foundation news [时间]`
- `CNCF updates [时间]`

**开源项目/工具（tool/project）：**
- `GitHub trending DevOps`
- `GitHub trending AI`
- `DevOps tools 2026`
- `AI developer tools`
- `CI/CD automation tools`
- `MLOps tools`
- `site:github.com awesome-devops`

**学习资源（resource）：**
- `DevOps tutorial [时间]`
- `AI engineering course`
- `Kubernetes best practices`
- `CI/CD guide`
- `site:freecodecamp.org DevOps`

**综合搜索：**
- Hacker News: `site:news.ycombinator.com DevOps`
- Reddit DevOps: `site:reddit.com/r/devops`
- Reddit ML: `site:reddit.com/r/MachineLearning`

### 2. 执行搜索

使用 Web Search 工具搜索每个来源，收集最近发布的高质量内容。

### 3. 筛选和验证 ⭐ 强化真实性

对搜索结果进行筛选：
- ✅ **检查发布日期是否在指定时间范围内**（这是最关键的验证）
  - 必须从页面中提取真实的发布日期
  - 不得使用搜索结果中的日期（可能不准确）
  - 如果无法确定发布日期，不要使用该内容
- ✅ **验证内容质量**（是否有实践案例、代码示例、深度分析）
- ✅ **优先选择知名平台和公司官方博客**
  - 官方来源：AWS Blog, Google Blog, Microsoft Blog, GitHub Blog 等
  - 知名技术媒体：The Verge, TechCrunch, Ars Technica, InfoQ 等
  - 技术社区：Medium, Dev.to（需验证作者）
- ✅ **验证链接可访问性**
  - 每个链接都必须能访问（HTTP 200）
  - 使用最终 URL，避免重定向链接
- ✅ **验证内容真实性**
  - 标题与页面内容匹配
  - 关键事实有依据（公司名、产品名、数字等）
  - 对于重大新闻，交叉验证其他来源
- ❌ **排除营销软文和低质量内容**
- ❌ **排除无法访问的链接**
- ❌ **排除时间范围外的内容**

**真实性验证清单**：
- [ ] 发布日期已从页面提取并确认在时间范围内
- [ ] 链接可访问（已测试）
- [ ] 来源可信（官方或知名平台）
- [ ] 内容与标题匹配
- [ ] 无编造或夸大的内容

### 4. 提取关键信息

对每条内容提取：
- 标题
- 原始链接（非重定向链接）
- **发布日期**（必须从页面中提取真实日期，格式：YYYY-MM-DD）
- **发布日期验证**（说明日期来源：meta 标签、正文、URL 等）
- 来源平台/作者
- 内容摘要（50-100字）
- 推荐理由（为什么值得关注）
- **可信度评级**（官方来源/知名平台/社区来源）

**日期提取方法**（优先级从高到低）：
1. HTML meta 标签：`<meta property="article:published_time">`
2. JSON-LD 结构化数据：`"datePublished"`
3. 页面正文中的明确日期标注
4. URL 路径中的日期（如 `/2026/01/20/article`）

**如果无法确定发布日期**：
- 不要猜测或使用搜索结果中的日期
- 不要使用该内容
- 在报告中说明原因

## 输出

返回结构化的内容列表：

```json
{
  "content_type": "blog",
  "time_range": "2026-01-11 至 2026-01-18",
  "items": [
    {
      "title": "文章标题",
      "url": "https://...",
      "source": "Medium / AWS Blog / etc.",
      "published_date": "2026-01-15",
      "date_source": "meta标签: article:published_time",
      "date_verified": true,
      "url_accessible": true,
      "credibility": "官方来源",
      "summary": "内容摘要，50-100字",
      "why_matters": "为什么值得关注的理由",
      "language": "英文/中文"
    }
  ],
  "search_queries_used": ["使用的搜索查询列表"],
  "total_found": 10,
  "verification_summary": {
    "total_searched": 20,
    "passed_verification": 10,
    "failed_time_check": 5,
    "failed_access_check": 3,
    "failed_quality_check": 2
  }
}
```

## 质量标准

- **真实性第一**：所有内容必须经过发布日期和链接可访问性验证
- **时效性严格**：发布日期必须在指定时间范围内，不得使用范围外的内容
- **来源可靠**：优先官方博客和知名技术媒体
- 博客文章必须包含实践案例、代码示例或架构图
- 新闻必须来自可信来源，有事实依据
- 工具/项目必须是活跃维护的，有实际使用价值
- 所有内容必须与 DevOps/AI/CI/CD/Build 领域相关
- 优先推荐大公司官方博客和知名技术平台的内容
