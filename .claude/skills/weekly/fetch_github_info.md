---
name: fetch-github-info
description: Fetches detailed GitHub repository information including accurate star count, fork count, description, primary language, and last update time. Use when the user mentions GitHub projects, needs to verify repository stats, or requires accurate project information for the weekly newsletter.
metadata:
  author: shenxianpeng
  version: "1.1"
---

# 获取 GitHub 项目信息

获取 GitHub 开源项目的详细信息，包括 Star 数、描述、最新更新时间等真实数据。

## 输入
- `repo_url`: GitHub 仓库 URL（如 `https://github.com/owner/repo`）
- 或 `repo_full_name`: 仓库全名（如 `owner/repo`）

## 过程

### 1. 解析仓库信息

从 URL 或全名中提取：
- Owner（所有者）
- Repository name（仓库名）

示例：
- `https://github.com/kubernetes/kubernetes` → owner: `kubernetes`, repo: `kubernetes`
- `microsoft/vscode` → owner: `microsoft`, repo: `vscode`

### 2. 访问 GitHub 页面

访问 GitHub 仓库主页：`https://github.com/{owner}/{repo}`

### 3. 提取关键信息

从页面中提取以下信息：
- ⭐ **Star 数**：实际的 Star 数量（如 12,345）
- 📝 **描述**：项目的简短描述
- 🏷️ **主要语言**：项目使用的主要编程语言
- 🔄 **最后更新**：最近一次提交的时间
- 📊 **Fork 数**：Fork 数量
- 👀 **Watch 数**：关注者数量
- ⚡ **Topics/Tags**：项目标签
- 📄 **License**：开源协议
- 🔗 **主页 URL**：项目主页（如果有）

### 4. 验证项目活跃度

检查项目是否值得推荐：
- ✅ 最近 6 个月内有更新
- ✅ Star 数 > 100（根据项目类型可调整）
- ✅ 有完整的 README 文档
- ✅ 有实际的代码提交，非空项目
- ❌ 标记为 archived 的项目通常不推荐

### 5. 格式化输出

整理成适合周刊使用的格式。

## 输出

返回结构化的项目信息：

```json
{
  "repo_name": "kubernetes/kubernetes",
  "repo_url": "https://github.com/kubernetes/kubernetes",
  "stars": 112345,
  "forks": 38765,
  "description": "Production-Grade Container Orchestration",
  "language": "Go",
  "last_updated": "2026-01-17",
  "homepage": "https://kubernetes.io",
  "topics": ["kubernetes", "containers", "orchestration", "devops"],
  "license": "Apache-2.0",
  "is_active": true,
  "is_archived": false,
  "weekly_formatted": "[kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)\n\nProduction-Grade Container Orchestration。这个项目...\n\n⭐ Star 数：112,345"
}
```

## 错误处理

如果遇到以下情况：
- ❌ 仓库不存在（404）：返回错误，不包含在推荐中
- ❌ 访问受限（private repo）：返回错误
- ❌ 项目已归档（archived）：标记为不推荐
- ⚠️ 无法获取某些信息：使用 "N/A" 但仍可推荐项目

## 注意事项

- **绝对不要**编造 Star 数或其他数据
- 如果无法访问 GitHub，返回明确的错误信息
- Star 数要格式化为易读格式（如 12,345 而不是 12345）
- 确保返回的是最终的 GitHub URL，不是重定向链接
