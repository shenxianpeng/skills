# Daily Skills - 深度文章创作

用于撰写微信公众号深度思考文章的 GitHub Copilot Skills 集合。

## 📋 Skills 概览

| Skill | 描述 | 使用场景 |
|-------|------|----------|
| [write_deep_article.md](write_deep_article.md) | 撰写深度思考文章 | 基于真实事件创作有深度的原创文章 |
| [verify_content_authenticity.md](verify_content_authenticity.md) | 验证内容真实性 | 交叉验证文章中的所有事实和数据 |

## 🎯 核心理念

### 内容定位
- **主题**: AI 技术与应用（70%），DevOps 实践（30%）
- **深度**: 超越表面信息，提供独特见解
- **真实**: 所有内容基于可验证的真实事件
- **原创**: 展现个人思考，而非信息搬运

### 质量标准
- ✅ **可验证性**: 所有事实、数据都有明确来源
- ✅ **去 AI 化**: 避免 AI 生成内容的典型特征
- ✅ **有深度**: 提供超越常规解读的分析
- ✅ **可读性**: 符合微信公众号阅读习惯

## 🚀 快速开始

### 创作一篇深度文章

```
@workspace #file:write_deep_article.md
请写一篇关于 [主题] 的深度分析文章
- topic: [具体主题]
- article_type: [trend_analysis/case_study/tech_insight/comparison/reflection]
- target_length: [字数，默认 2000-3000]
```

### 文章类型说明

- **trend_analysis**: 行业趋势分析
  - 适用于：技术趋势、市场变化、行业动态
  - 示例：AI 大模型价格战的深层逻辑

- **case_study**: 案例深度解析
  - 适用于：公司实践、项目案例、技术应用
  - 示例：Netflix 如何用 AI 优化推荐系统

- **tech_insight**: 技术洞察与思考
  - 适用于：技术原理、工具评测、方法论
  - 示例：AI 编程助手对开发者的真实影响

- **comparison**: 对比分析
  - 适用于：技术选型、产品对比、方案评估
  - 示例：Claude vs GPT-4：谁更适合代码生成？

- **reflection**: 反思与展望
  - 适用于：个人思考、行业观察、未来展望
  - 示例：我们可能高估了 AI Agent 的实用性

## 📝 创作流程

### 1. 信息收集（30 分钟）
- 搜索 15+ 个相关来源
- 涵盖官方、媒体、学术、社区等多个渠道
- 收集正反两方面观点

### 2. 内容验证（自动）
- 验证所有链接可访问性
- 确认发布日期准确性
- 评估来源可信度
- 交叉验证关键信息

### 3. 撰写初稿（60 分钟）
- 构建文章框架
- 撰写各个章节
- 去 AI 化处理
- 增加个人思考

### 4. 审查优化（30 分钟）
- 事实核查
- 质量检查
- 可读性优化
- 原创性确认

## 💡 使用示例

### 示例 1：分析热点事件

```
@workspace #file:write_deep_article.md
写一篇关于 OpenAI 发布 O3 模型的深度分析

- topic: OpenAI O3 模型发布解读
- article_type: trend_analysis
- reference_links:
  - https://openai.com/blog/...
  - https://techcrunch.com/...
- target_length: 2500
```

**输出**：
- 文章文件：`output/daily/2026-01-31-openai-o3-analysis.md`
- 验证报告：包含所有引用来源的验证记录
- 参考资料：15+ 个已验证的来源

### 示例 2：技术洞察

```
@workspace #file:write_deep_article.md
写一篇关于 AI 编程助手实际影响的思考文章

- topic: AI 编程助手的真实影响
- article_type: tech_insight
```

**输出**：
- 基于真实数据和案例的深度分析
- 包含个人实践经验和思考
- 避免常见的 AI 生成痕迹

### 示例 3：案例分析

```
@workspace #file:write_deep_article.md
分析 Anthropic 如何构建 Claude 的安全机制

- topic: Claude 安全机制深度解析
- article_type: case_study
- reference_links:
  - https://www.anthropic.com/...
```

## ⚠️ 重要提示

### 必须做的
- ✅ 验证所有事实和数据
- ✅ 标注所有引用来源
- ✅ 提供独特见解
- ✅ 展现个人思考
- ✅ 符合微信公众号规范

### 绝对禁止
- ❌ 编造数据或案例
- ❌ 未经验证就引用
- ❌ 抄袭他人内容
- ❌ 使用典型的 AI 套话
- ❌ 发布未经审查的内容

## 📊 质量指标

### 文章质量评估

**内容质量**（满分 100）：
- 真实性（30 分）：所有信息可验证
- 深度（25 分）：超越表面分析
- 原创性（25 分）：有独特见解
- 实用性（20 分）：对读者有启发

**写作质量**（满分 100）：
- 可读性（30 分）：符合公众号习惯
- 去 AI 化（30 分）：无明显 AI 痕迹
- 逻辑性（20 分）：论证链条完整
- 吸引力（20 分）：标题和开头吸引人

**目标**: 两项均 ≥ 80 分

## 🔄 持续改进

### 收集反馈
- 阅读量、点赞数
- 读者评论
- 同行评价
- 事实错误报告

### 优化方向
- 写作风格调整
- 验证流程优化
- 主题选择策略
- 案例库建设

## 📚 参考资源

### 推荐阅读
- **写作技巧**: [write_deep_article.md](write_deep_article.md) 附录部分
- **验证方法**: [verify_content_authenticity.md](verify_content_authenticity.md)

### 信息来源
**一级来源**（优先使用）：
- 官方博客：OpenAI, Anthropic, Google AI, Microsoft
- 学术平台：arXiv, Papers with Code
- 权威媒体：TechCrunch, The Verge, MIT Tech Review
- 技术大牛：知名专家的个人博客

**二级来源**（需验证）：
- 技术社区：Medium, Dev.to, Hacker News
- 科技媒体：36Kr, InfoQ
- 公司博客：Netflix, Airbnb 等技术博客

## 🛠️ 工具支持

### 验证工具
- 链接检查：`curl`, `wget`
- 网页快照：Wayback Machine
- 来源查证：Google Scholar, Crunchbase

### 写作辅助
- 语法检查：Grammarly（英文）
- 排版优化：微信公众号编辑器
- 图片处理：Figma, Canva

## 📄 输出规范

### 文件结构
```
output/daily/YYYY-MM-DD-{topic-slug}.md
├── Front Matter（元数据）
├── 文章正文
├── 参考资料
└── 验证记录
```

### Front Matter
```yaml
---
title: 文章标题
date: YYYY-MM-DD
category: AI/DevOps
tags: [标签1, 标签2, 标签3]
verified: true
word_count: 实际字数
---
```

## 🎓 最佳实践

### 选题建议
1. **热点事件**: 发布后 3-7 天内（有足够信息，但还有讨论热度）
2. **技术趋势**: 有多个案例支撑的趋势
3. **个人思考**: 基于实践的独特观察
4. **案例分析**: 有公开资料的典型案例

### 写作技巧
1. **开头**: 用具体场景或数据引入
2. **论证**: 观点-论据-案例三段式
3. **过渡**: 自然流畅，避免生硬
4. **结尾**: 开放式，而非总结式

### 验证重点
1. **数据**: 必须有原始来源
2. **引用**: 不能断章取义
3. **时间**: 发布日期准确
4. **来源**: 可信度 ≥ 三星

---

## 更新日志

### v1.0 (2026-01-31)
- ✨ 创建 write_deep_article skill
- ✨ 创建 verify_content_authenticity skill
- 📝 完善文档和示例

---

**开始使用**: `@workspace #file:write_deep_article.md [你的主题]`
