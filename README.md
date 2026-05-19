# 华东交通大学 2023 级软件工程实训

本仓库是华东交通大学 2023 级软件工程专业实训的每日作业汇总，每天一个独立项目，循序渐进地学习 AI 辅助软件开发。

仓库地址：[git@github.com:xiongchaoyong/EJTCU-Practical-Training.git](https://github.com/xiongchaoyong/EJTCU-Practical-Training)

## 项目列表

### Day01 — RSS 聚合器

基于 AI 大模型的新闻聚合工具。自动抓取多个 RSS 源的最新文章，调用 AI 生成中文要点总结，输出 Markdown 日报。

- **后端**：Python + FastAPI + SQLite + APScheduler
- **前端**：Vue 3 + Element Plus + Vite
- **AI 服务**：兼容 OpenAI 接口（支持 OpenAI / DeepSeek 等）
- **核心流程**：RSS 抓取 → AI 摘要 → Markdown 日报生成

### Day02 — Agentic 工作流

基于 Claude Code 的 AI 辅助需求分析系统。以"基于图像特征识别的宠物领养平台"为案例，构建智能体+技能协作的需求分析工作流。

- **开发理念**：Plan → Execute 工作流，AI 从代码补全升级为协作团队
- **核心内容**：
  - Vibe Coding 核心工作流（规划先行，执行在后）
  - Agentic 数字团队（多智能体角色分工与协作）
  - 需求澄清技能（100 分评分制，≥90 分方可进入开发）
  - 产品经理智能体（需求分析 → PRD 生成）
- **输出产物**：标准化的 PRD 文档、需求澄清记录
