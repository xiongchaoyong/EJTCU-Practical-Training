# 每日新闻聚合器

自动抓取多个 RSS 源的最新文章，调用 AI 大模型生成中文要点总结，生成 Markdown 日报。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python + FastAPI |
| 前端框架 | Vue 3 + Element Plus |
| AI 服务 | 兼容 OpenAI 接口（支持 OpenAI / DeepSeek / 自定义） |
| RSS 解析 | feedparser + httpx（15 秒超时） |
| 定时任务 | APScheduler（每 6 小时） |
| 数据存储 | SQLite + SQLAlchemy ORM |
| 加密存储 | Fernet 对称加密（API Key） |
| 构建工具 | Vite |

## 项目结构

```
实训/
├── backend/
│   ├── main.py                   # FastAPI 入口，CORS，lifespan
│   ├── config.py                 # Fernet 加密 / 解密工具
│   ├── database.py               # SQLite 连接，表初始化
│   ├── models.py                 # ORM：RSSSource, Article, DailyReport, AppConfig
│   ├── schemas.py                # Pydantic 请求/响应模型
│   ├── scheduler.py              # APScheduler（每 6 小时）
│   ├── requirements.txt
│   ├── routes/
│   │   ├── sources.py            # RSS 源 CRUD + 推荐 + 批量添加
│   │   ├── fetch.py              # 手动触发抓取 + 任务状态查询
│   │   ├── latest.py             # 日报查询、列表、下载
│   │   └── settings.py           # AI 接口配置（多提供商）
│   └── services/
│       ├── rss_fetcher.py        # httpx 取 Feed → feedparser 解析 → 去重入库
│       ├── summarizer.py         # AI 摘要（可配置 base_url / model）
│       ├── report.py             # Markdown 日报生成 + 全流程编排
│       ├── task_store.py         # 任务状态内存追踪
│       └── recommendations.py    # 6 分类 26 个精选 RSS 源
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js            # 开发代理 /api → 127.0.0.1:8000
    └── src/
        ├── main.js
        ├── App.vue               # 主布局 + AI 配置弹窗 + Key 状态指示
        ├── api/index.js          # Axios API 封装
        └── components/
            ├── SourceManager.vue  # 抽屉：RSS 源增删改查 + 推荐源浏览
            ├── FetchTrigger.vue   # 弹窗：触发抓取 + 进度轮询 + 结果展示
            └── DailyReport.vue    # 日报渲染/源码切换 + 下载（主区域占满）
```

## 启动方式

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API 运行在 http://127.0.0.1:8000

### 前端

```bash
cd frontend
npm install
npm run dev
```

页面运行在 http://localhost:3000（Vite 自动代理 `/api` 到后端）

## 使用流程

1. 点右上角 **设置 API Key**，选择提供商（OpenAI / DeepSeek / 自定义），填入 Key、接口地址、模型名
2. 点 **RSS 源管理** 打开右侧抽屉，浏览推荐源勾选批量添加，或手动输入
3. 点 **抓取与总结**，弹窗显示实时进度，完成后日报自动刷新，无需手动操作
4. 日报支持**渲染模式**和**源码模式**切换，可下载 `.md` 文件
5. 系统每 6 小时自动执行一次（右上角 Key 状态标签常驻显示是否已配置）

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sources` | 获取所有 RSS 源 |
| POST | `/api/sources` | 添加 RSS 源 |
| PUT | `/api/sources/{id}` | 修改 RSS 源 |
| DELETE | `/api/sources/{id}` | 删除 RSS 源 |
| GET | `/api/sources/recommendations` | 获取分类推荐 RSS 源 |
| POST | `/api/sources/bulk-add` | 批量添加推荐源 |
| POST | `/api/fetch` | 触发抓取+总结（异步，返回 task_id） |
| GET | `/api/task/{task_id}` | 查询任务进度与结果 |
| GET | `/api/latest` | 获取最新日报 |
| GET | `/api/reports` | 历史日报列表（最近 20 条） |
| GET | `/api/report/{id}/download` | 下载指定日报 Markdown 文件 |
| POST | `/api/set-openai-key` | 配置 AI 接口（Key + 端点 + 模型） |
| GET | `/api/check-openai-key` | 查询当前 AI 配置状态 |

## 页面布局

- 顶部导航栏：标题 + **Key 配置状态标签**（绿色已配置/红色未设置）+ 配置按钮
- 工具栏：RSS 源管理按钮 + 抓取与总结按钮
- 主区域：日报预览（`flex: 1` 占满剩余空间），支持渲染/源码切换和下载
- RSS 源管理：**右侧抽屉**（720px），表格最大高度 520px 可滚动，推荐源分类折叠面板
- 抓取任务：**弹窗**触发，轮询任务进度，展示详细结果后自动关闭并刷新日报

## 核心设计

### RSS 抓取
- httpx 先获取 Feed 内容（15 秒超时），再交给 feedparser 解析，避免卡死
- 每个源取最新 10 篇，按发布时间倒序，按链接去重
- 发布时间存储为 timezone-aware UTC，展示转换为北京时间
- 单源失败（超时、解析错误）不影响其他源

### AI 总结
- 兼容 OpenAI 接口协议，支持切换提供商（OpenAI / DeepSeek / 自定义端点）
- 系统提示词要求中文总结 1-2 句话，不超过 50 字
- 输入：文章标题 + 内容摘要（HTML 标签清洗后取前 500 字符）
- SDK 超时 10 秒，关闭自动重试，单篇失败不影响后续
- 错误信息按状态码转为中文提示（Key 无效 / 超时 / 限流 / 网络错误）
- API Key 经 Fernet 加密存储，base_url 和 model 明文存储

### 任务追踪
- 任务状态存储于内存，`POST /api/fetch` 返回 task_id
- 前端每 3 秒轮询 `GET /api/task/{task_id}`，显示实时阶段（抓取中 / AI 总结中）
- 完成后自动展示结果：源数、文章数、总结成功/失败数，日报同步刷新
- 定时任务同样生成 task_id 并追踪

### Markdown 日报
- 按 RSS 来源分组，每组间 `---` 分隔
- 每篇：标题链接 + AI 要点 / 失败原因 + 发布时间（北京时间）
- 元信息：文章数、源数、生成时间、触发方式（手动/定时）
- 日报存储数据库，可回溯历史

### 定时任务
- APScheduler 后台线程，每 6 小时自动执行
- 完整流程：抓取 RSS → AI 总结 → 生成日报

### RSS 源智能推荐
- 内置 6 个分类 26 个精选源：
  - 科技资讯（8）：36氪、少数派、TechCrunch、WIRED、Hacker News 等
  - 开发者技术（6）：阮一峰、GitHub Trending、Dev.to、Python 官方博客等
  - 财经商业（3）：雪球、华尔街见闻、哈佛商业评论
  - 综合新闻（3）：BBC 中文、澎湃新闻、路透社
  - 科学科普（4）：果壳网、NASA、Nature、ScienceDaily
  - 设计创意（2）：优设网、Dribbble
- 分类折叠面板，勾选批量添加，已添加自动标记
