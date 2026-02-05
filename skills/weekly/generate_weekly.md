---
name: generate-weekly
description: Automatically generates a complete tech weekly newsletter with objective, neutral style covering software development, DevOps, AI, and IT industry trends. Follows Ruan Yifeng's weekly format - data-driven, broad coverage, clear structure.
metadata:
  author: shenxianpeng
  version: "3.0"
---

# 生成攻城狮周刊

自动生成《攻城狮周刊》，以客观中立的视角记录每周技术动态、深度文章、实用工具和学习资源。

## 输入
- `week_number`：期数（如第 3 期）
- `start_date`：开始日期（格式：YYYY-MM-DD）
- `end_date`：结束日期（格式：YYYY-MM-DD）

## 文件路径规则

根据当前年份自动确定周刊存储路径：
- 路径格式：`output/weekly/{YEAR}/weekly-{week_number}/index.md`
- 年份从 `start_date` 或 `end_date` 中提取
- 示例：2026 年第 3 期 → `output/weekly/2026/weekly-3/index.md`
- 所有相关图片（封面图、章节图片等）保存在同一目录下

## 核心理念

- **客观中立优先** ⭐：像观察者而非参与者，用数据说话，避免主观臆断
- **覆盖面广**：不局限于单一领域，涵盖技术、产品、行业、趋势等多维度
- **真实性第一** ⭐：所有内容基于真实搜索，严禁编造，必须验证发布时间和来源
- **内容自证** ⭐：每条内容都必须能证明其真实性、时效性和来源可靠性
- **严格去重** ⭐：检查历史周刊，避免推荐重复内容
- **数据驱动**：用具体数字、统计、案例支撑观点
- **中文全角标点** ⭐：所有中文内容必须使用全角标点符号（：，。、！？""「」等）
- **简洁准确**：描述清晰简洁，突出关键信息
- **参考格式** ⭐：严格参照 `skills/weekly/references/week_demo.md` 的格式和风格

## 过程

### 步骤 1：收集各类内容

使用网页搜索从以下可信来源收集内容：

**来源列表**：
- **技术新闻**：InfoQ、GitHub Blog、TechCrunch、The Verge、Ars Technica
- **技术博客**：AWS Blog、Google Cloud Blog、Microsoft DevBlogs、Medium、Dev.to
- **开发者社区**：Hacker News、Reddit r/programming
- **GitHub Trending**：热门开源项目
- **行业报告**：Gartner、ThoughtWorks Technology Radar、InfoQ Trends

**内容分类**：

1. **行业动态**（5-8 条）
   - 时间范围：最近 7 天
   - 搜索关键词：developer news、software engineering、DevOps、AI、tech industry
   - 标准：有具体数字、日期、官方来源，影响范围广

2. **深度阅读**（3-5 篇）
   - 时间范围：最近 7 天
   - 搜索关键词：technical articles、software development、engineering practices
   - 标准：1500+ 字，有深度洞察，数据支撑

3. **效率工具**（3-5 个）
   - 时间范围：最近 30 天
   - 搜索关键词：developer tools、productivity tools、automation
   - 标准：实用性强，有文档，活跃维护

4. **开源项目**（2-3 个）
   - 时间范围：GitHub Trending
   - 搜索关键词：trending repositories、popular open source
   - 标准：Stars > 500 或增长快速，代码质量高

5. **学习资源**（1-2 个）
   - 时间范围：最近 30 天
   - 搜索关键词：programming tutorials、tech courses、technical books
   - 标准：内容系统，来源可靠，免费或有试用

### 步骤 2：验证 GitHub 项目

对所有涉及的 GitHub 项目：
- 获取真实的 Star 数
- 验证项目是否活跃
- 确保项目可访问

### 步骤 3：验证内容真实性 ⭐

严格验证每条内容：

**验证维度**：
1. **访问验证**：每个链接都必须可访问（HTTP 200）
2. **时间验证**：发布日期在 `[start_date, end_date]` 范围内
3. **内容验证**：标题与实际页面一致
4. **来源验证**：优先官方来源和知名媒体

**自证要求**：
- 必须能证明每条内容的发布日期在周刊时间范围内
- 必须注明具体来源和链接
- 有争议的内容要多源交叉验证

### 步骤 3.5：内容去重检查

**这是确保周刊质量的关键步骤！**

扫描历史周刊（`output/weekly/` 下所有已发布期数），检查：

1. **URL 精确匹配**：完全相同的链接视为重复
2. **标题相似度**：> 80% 相似的标题可能是重复内容
3. **GitHub 项目重复**：同一个 GitHub 仓库不重复推荐

**去重策略**：
- 完全重复 → 立即移除，寻找替代内容
- 同项目重大更新（时隔 ≥ 4 周）→ 可保留，但需注明"更新"
- 不同角度报道同一事件 → 评估价值，择优保留

**替代方案**：
- 自动搜索同类但未推荐的内容
- 扩大搜索时间范围至 2 周
- 调整搜索关键词

### 步骤 4：批量验证链接

使用 verify_links skill 批量验证所有链接的可访问性。

### 步骤 5：选择本周话题

从本周最重要的技术事件中选择一个作为话题：
- 影响范围最广的技术趋势
- 引发行业讨论的事件
- 值得深度分析的现象

**话题撰写要求**（300-500 字）：
1. **现象描述**：用数据和事实说明发生了什么
2. **多角度分析**：技术、产品、市场、用户等维度
3. **趋势判断**：基于事实的理性预测
4. **保持中立**：避免情绪化表达，让读者自己判断

**注意**：
- 不使用"我认为"、"我觉得"等第一人称
- 用"数据显示"、"报告指出"、"业界认为"等客观表达
- 多引用具体数字、案例、引言

### 步骤 6：下载所有图片

创建 `images.json` 文件，定义所有需要的图片：
- featured.png（封面图）
- news-1.png 到 news-N.png
- blog-1.png 到 blog-N.png
- tool-1.png 到 tool-N.png
- ai-1.png 到 ai-N.png
- resource-1.png

使用 Unsplash 高质量图片，URL 格式：
```
https://images.unsplash.com/photo-{ID}?w=800&h=450&fit=crop
```

然后运行：
```bash
python3 skills/weekly/scripts/download_weekly_images.py {year} {week_number} output/weekly/{year}/weekly-{week_number}/images.json
```

### 步骤 7：撰写周刊正文

**严格按照 `skills/weekly/references/week_demo.md` 的格式输出**：

```markdown
---
title: 攻城狮周刊（第 X 期）：[主标题]
summary: 这里记录每周值得分享的技术内容，周五发布。本杂志开源，欢迎投稿。
tags: 
  - Weekly
translate: false
authors: 
  - shenxianpeng
date: YYYY-MM-DD
---

这里记录每周值得分享的技术内容，周五发布。

本杂志[开源](https://github.com/shenxianpeng/weekly)，欢迎[投稿](https://github.com/shenxianpeng/weekly/issues)。合作请[邮件联系](mailto:xianpeng.shen@gmail.com)（xianpeng.shen@gmail.com）。

## 本周封面

![封面图](featured.png)

[1-2 句话说明封面内容]

## [本周话题标题]

[300-500 字客观分析，包含：
1. 现象描述：本周技术领域的重要趋势或事件
2. 数据支撑：用具体数字、案例说明
3. 多角度观察：技术、产品、市场等维度
4. 趋势判断：基于事实的理性分析

注意：
- 使用全角标点：，。！？：；""
- 避免主观情绪化表达
- 保持观察者视角
- 用数据和事实说话]

## 行业动态

1、**[新闻标题]**

![配图](news-1.png)

[80-120 字客观描述，包含：
- 关键事实和数据
- 发生时间
- 影响范围
- 来源说明

格式要求：
- 使用全角标点
- 避免"非常"、"极其"等主观形容
- 突出关键数字和日期]

2、[**[新闻标题](链接)**]

![配图](news-2.png)

[80-120 字客观描述]

[重复 5-8 条，格式保持一致]

## 深度阅读

1、[**[文章标题](链接)**]

![配图](blog-1.png)

[120-180 字内容概括，包含：
- 文章核心观点
- 关键数据和案例
- 主要论述逻辑
- 适合读者群体

格式要求：
- 客观转述，不加主观评价
- 突出文章的数据和结论
- 说明文章的实用价值]

[重复 3-5 篇]

## 效率工具

1、**[工具名](链接)**

![配图](tool-1.png)

[80-120 字功能介绍，包含：
- 主要功能
- 技术特点
- 适用场景
- 开源/商业说明

格式要求：
- 客观说明功能
- 不夸大效果
- 提供具体使用场景]

[重复 3-5 个]

## 开源项目

1、**[项目名称](链接)**

![配图](ai-1.png)

[100-150 字项目介绍，包含：
- 项目功能
- 技术特点
- 应用场景
- 开发现状

格式要求：
- 突出项目特色
- 说明技术优势
- 提供使用参考]

[重复 2-3 个]

## 学习资源

1、[资源标题](链接)

![配图](resource-1.png)

[80-120 字资源介绍，包含：
- 内容范围
- 适合人群
- 学习价值
- 免费/付费说明

格式要求：
- 明确内容定位
- 说明适用对象
- 强调实用价值]

[重复 1-2 个]

## 精彩摘要

1、"[引用内容，使用全角引号]"
—— [出处/作者]

2、"[引用内容]"
—— [出处/作者]

[收录 3-5 条精彩观点，要求：
- 有启发性或代表性
- 来自本期推荐的文章
- 准确引用，注明出处]

## 行业观点

1、[观点陈述]
—— [来源/作者]

[80-150 字客观分析，包含：
- 观点的背景
- 观点的代表性
- 可能的影响
- 业界反应

格式要求：
- 客观陈述，不站队
- 提供背景信息
- 说明观点的意义]

[收录 1-2 个有代表性的观点]

（完）
```

## 重要提醒

1. **中文标点符号**：
   - 全角：，。！？：；""「」（）【】
   - 半角仅用于英文内容和代码
   
2. **客观中立原则**：
   - 避免"我认为"、"我觉得"
   - 用"数据显示"、"报告指出"
   - 多引用权威来源

3. **格式严格对照**：
   - 参考 week_demo.md
   - 标题层级一致
   - 图片命名规范
   - 章节顺序固定

4. **内容质量**：
   - 事实准确，来源可信
   - 数据真实，时间准确
   - 描述简洁，信息完整
   - 去重严格，无重复推荐

## 输出

- Markdown 文件：`output/weekly/{year}/weekly-{week_number}/index.md`
- 图片文件：所有图片在同一目录下
- 图片配置：`images.json`（用于批量下载）

## 示例

参考 `skills/weekly/references/week_demo.md` 查看完整格式示例。
