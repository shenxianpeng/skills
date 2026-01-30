---
name: weekly
description: 自动化生成《攻城狮周刊》的完整工具集，涵盖技术内容搜索、GitHub 项目信息获取、链接验证、图片下载等。关注 AI、DevOps、开源、科技巨头动态等领域。Use when generating tech weekly newsletter, searching AI/DevOps/open-source content, or managing weekly publication workflow.
metadata:
  author: shenxianpeng
  version: "1.1"
---

# 攻城狮周刊生成 Skills

这是一套用于自动化生成《攻城狮周刊》的 GitHub Copilot Skills 集合。

关注领域：AI、DevOps、开源动态、科技巨头（Google、Microsoft、AWS、Meta 等）、工程效率、CI/CD、云原生等。

## 📋 Skills 清单

### 1. [generate_weekly.md](generate_weekly.md) - 生成周刊（主流程）

**用途**：自动生成完整的攻城狮周刊

**输入**：
- `week_number`: 期数（如第 3 期）
- `start_date`: 开始日期（YYYY-MM-DD）
- `end_date`: 结束日期（YYYY-MM-DD）

**使用示例**：
```
@workspace #file:weekly/generate_weekly.md 请生成第 3 期攻城狮周刊
- week_number: 3
- start_date: 2026-01-11
- end_date: 2026-01-17
```

**输出**：完整的周刊 Markdown 文件（包含 Hugo Front Matter），保存在 `output/weekly/{YEAR}/weekly-{week_number}/index.md`

---

### 2. [search_tech_content.md](search_tech_content.md) - 搜索技术内容

**用途**：搜索 DevOps、AI、CI/CD 和 Build 领域的技术内容

**输入**：
- `content_type`: 内容类型（news/blog/tool/project）
- `keywords`: 搜索关键词
- `time_range`: 时间范围（如 "最近 7 天"）
- `count`: 期望数量（可选，默认 5-10 条）

**使用示例**：
```
@workspace #file:weekly/search_tech_content.md 搜索最近 7 天的 DevOps 新闻，关键词：Kubernetes, Docker
```

**输出**：结构化的技术内容列表，包括标题、URL、描述和发布日期

---

### 3. [fetch_github_info.md](fetch_github_info.md) - 获取 GitHub 项目信息

**用途**：获取 GitHub 开源项目的真实数据（Star 数、描述等）

**输入**：
- `repo_url`: GitHub 仓库 URL（如 `https://github.com/owner/repo`）
- 或 `repo_full_name`: 仓库全名（如 `owner/repo`）

**使用示例**：
```
@workspace #file:weekly/fetch_github_info.md 获取 kubernetes/kubernetes 的项目信息
```

**输出**：
- ⭐ Star 数
- 📝 项目描述
- 🏷️ 主要编程语言
- 🔄 最后更新时间
- 📊 Fork 数、Watch 数
- 🔗 项目主页 URL
- ⚡ Topics/Tags
- 📄 License

---

### 4. [verify_links.md](verify_links.md) - 验证链接有效性

**用途**：批量验证链接是否可访问，避免周刊中出现失效链接

**输入**：
- `links`: 需要验证的 URL 列表

**使用示例**：
```
@workspace #file:weekly/verify_links.md 验证以下链接的有效性：
- https://example.com/article1
- https://github.com/user/repo
```

**输出**：
- ✅ 有效链接列表（HTTP 200-299）
- ❌ 失效链接列表（HTTP 404, 500 等）
- ⚠️ 需要注意的链接（重定向、超时等）

---

### 5. [download_images.md](download_images.md) - 下载和管理图片

**用途**：为周刊下载相关图片，增强可读性和吸引力

**输入**：
- `weekly_path`: 周刊目录路径（如 `output/weekly/2026/weekly-3/`）
- `content_sections`: 周刊内容的各个章节及其关键词

**使用示例**：
```
@workspace #file:weekly/download_images.md 下载图片到 output/weekly/2026/weekly-3/
```

**输出**：下载的图片文件，包括：
- `featured.png` - 封面图
- `news-1.png`, `news-2.png` - 行业动态图片
- `blog-1.jpg`, `blog-2.jpg` - 深度阅读图片
- `tool-1.png` - 效率工具图片
- `ai-1.png` - AI 项目图片

## 🔄 完整工作流程

1. **生成周刊主流程** → 调用 `generate_weekly.md`
   
2. **搜集内容阶段**
   - 调用 `search_tech_content.md` 搜索各类内容
   - 分别搜索：行业动态、深度阅读、效率工具、AI 项目

3. **验证和丰富数据**
   - 调用 `fetch_github_info.md` 获取 GitHub 项目真实数据
   - 调用 `verify_links.md` 验证所有链接有效性

4. **下载图片**
   - 调用 `download_images.md` 下载相关图片

5. **生成最终文件**
   - 整合所有内容生成 `index.md`
   - 包含 Hugo Front Matter

## 📂 输出文件结构

```
output/weekly/{YEAR}/weekly-{week_number}/
├── index.md           # 周刊内容（Hugo Markdown）
├── featured.png       # 封面图
├── news-1.png         # 行业动态图片
├── blog-1.jpg         # 深度阅读图片
├── tool-1.png         # 效率工具图片
└── ai-1.png           # AI 项目图片
```

## 💡 使用技巧

### 快速生成周刊

直接使用主流程 skill：
```
@workspace #file:weekly/generate_weekly.md 生成第 5 期周刊，时间是 2026-02-01 到 2026-02-07
```

### 单独更新某个章节

使用对应的 skill 单独搜索和更新：
```
@workspace #file:weekly/search_tech_content.md 搜索最新的 AI 工具项目
```

### 验证现有周刊的链接

```
@workspace #file:weekly/verify_links.md 验证 output/weekly/2026/weekly-3/index.md 中的所有链接
```

### 补充下载图片

```
@workspace #file:weekly/download_images.md 为 output/weekly/2026/weekly-3/ 补充下载缺失的图片
```

## ⚠️ 注意事项

1. **真实性第一**：所有内容基于真实搜索，禁止编造数据
2. **质量优于数量**：只推荐真正有价值的内容
3. **及时验证**：定期验证链接有效性，删除失效内容
4. **图片版权**：优先使用官方图片或开源图库（Unsplash、Pexels）
5. **年份自动识别**：会根据 `start_date` 或 `end_date` 自动确定年份路径

## 🎯 核心理念

- **自然呈现**：让内容自己说话，避免强制关联和刻意拔高
- **多元视角**：AI、DevOps、开源可以独立呈现，不必硬性关联
- **工程师视角**：提供实用洞察，而非宏大叙事
- **真实性第一**：所有内容基于真实搜索，不编造数据
- **高质量优先**：只推荐真正有价值的内容

## 📖 相关文档

- 项目说明：[../README.md](../README.md)
- 周刊主流程：[generate_weekly.md](generate_weekly.md)
- 内容搜索：[search_tech_content.md](search_tech_content.md)
- GitHub 信息：[fetch_github_info.md](fetch_github_info.md)
- 链接验证：[verify_links.md](verify_links.md)
- 图片管理：[download_images.md](download_images.md)
