---
name: check-content-duplicates
description: Check if the content (articles, tools, projects, resources) has already appeared in previous weekly issues to avoid repetition. This skill reads all historical weekly issues and maintains a database of used content.
metadata:
  author: shenxianpeng
  version: "1.0"
---

# 检查周刊内容重复

在生成新一期周刊之前，检查内容是否在历史周刊中已经出现过，避免重复推荐。

## 输入
- `content_list`: 待检查的内容列表，每项包含：
  - `type`: 内容类型（news/blog/tool/project/resource）
  - `title`: 标题
  - `url`: 链接
  - `description`: 描述（可选）
- `year`: 当前年份（如 2026）
- `week_number`: 当前期数（如 5）

## 过程

### 步骤 1：扫描历史周刊

1. 读取所有历史周刊文件：
   - 路径：`output/weekly/{year}/weekly-*/index.md`
   - 从 2026 年开始往前扫描

2. 提取每期周刊中的所有内容链接和标题

3. 建立去重数据库：
```json
{
  "urls": {
    "https://example.com/article": {
      "week": 3,
      "year": 2026,
      "title": "文章标题",
      "type": "blog"
    }
  },
  "titles": {
    "文章标题": {
      "week": 3,
      "year": 2026,
      "url": "https://example.com/article"
    }
  }
}
```

### 步骤 2：检查重复

对每一项待检查内容：

1. **URL 精确匹配**：
   - 检查 URL 是否完全相同
   - 考虑 URL 变体（带/不带 trailing slash，http/https）

2. **标题相似度匹配**：
   - 计算标题的相似度（使用编辑距离或关键词重合度）
   - 相似度 > 80% 视为重复

3. **同一项目/工具的不同文章**：
   - 检查是否是同一个项目的不同介绍文章
   - GitHub 项目：检查 repo owner/name
   - 开源工具：检查工具名称

### 步骤 3：生成检查报告

```markdown
## 内容重复检查报告

### ✅ 无重复内容 (N 条)
1. 标题 - URL - 类型

### ⚠️ 疑似重复 (N 条)
1. 标题 - URL
   - 相似内容：第 X 期，标题，URL
   - 相似度：85%
   - 建议：[替换/保留并说明]

### ❌ 确认重复 (N 条)
1. 标题 - URL
   - 重复内容：第 X 期
   - 建议：移除
```

## 去重策略

### 允许重复的情况

1. **同一工具/项目的重大更新**：
   - 间隔至少 4 周
   - 有重大版本更新或新功能
   - 需在描述中说明"此前在第 X 期介绍过"

2. **同一主题的不同角度文章**：
   - 不同作者的视角
   - 技术深度明显不同
   - 实践案例不同

3. **持续跟踪的热点**：
   - 重大技术趋势（如 AI Agent）
   - 需要持续关注的事件
   - 每次介绍都有新的进展

### 严格去重的情况

1. **完全相同的文章/链接**
2. **同一工具的常规介绍**（无重大更新）
3. **同样的新闻事件**
4. **同一教程/资源**

## 替代方案建议

当发现重复时，提供替代内容建议：

1. **搜索同类但未推荐的内容**：
   - 相同领域的其他优质文章
   - 相似功能的其他工具
   - 相关但未覆盖的主题

2. **扩展搜索范围**：
   - 稍微放宽时间限制
   - 扩展到相关技术领域
   - 查找不同来源的内容

## 输出

1. 重复检查报告（Markdown）
2. 清洗后的内容列表（移除确认重复的内容）
3. 替代内容建议列表（如有）

## 示例

```markdown
输入：
content_list:
  - type: tool
    title: "GitHub Copilot CLI"
    url: "https://github.blog/copilot-cli"
    
year: 2026
week_number: 5

检查结果：
❌ 确认重复
- 该工具已在第 3 期推荐（2026-01-30）
- URL: https://github.blog/ai-and-ml/github-copilot/power-agentic-workflows-in-your-terminal-with-github-copilot-cli/
- 建议：移除

替代建议：
1. GitHub Copilot SDK (未推荐过)
2. Continue.dev (AI 编程工具，未推荐过)
3. Cursor (AI IDE，未推荐过)
```

## 集成到周刊生成流程

在 `generate_weekly.md` 的步骤 3（验证内容真实性）之后，添加步骤 3.5：

```
步骤 3.5：检查内容重复
→ check_content_duplicates(content_list=[...], year=2026, week_number=5)
→ 移除重复内容
→ 根据建议补充替代内容
```

## 注意事项

- **自动化程度**：优先自动判断，疑似情况可以询问用户
- **历史数据维护**：每次生成新周刊后更新去重数据库
- **性能优化**：缓存历史周刊的元数据，避免重复读取
- **灵活性**：允许手动覆盖去重判断（用户明确要求时）
