# Gh Nexus - AI Agent Project Orchestration System

以GitHub Project为中心，使用gh命令管理，将注册的agent作为worker的自动化开发系统。

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Issue/PR                             │
│              (创建 Issue → 触发 Agent)                            │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Webhook
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Webhook Server :8080                          │
│              POST /webhook - GitHub事件接收                       │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Automation Engine                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Visionary │ │ Overseer │ │Interpreter│ │Dispatcher│           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │  Worker  │ │  Tester  │ │ Rewarder │                        │
│  └──────────┘ └──────────┘ └──────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Workers                                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                  │
│  │  opencode  │ │claude code│ │   cursor   │                  │
│  └────────────┘ └────────────┘ └────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 配置环境

```bash
# 复制环境配置
cp .env.example .env

# 编辑 .env 填写配置
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your-org
GITHUB_PROJECT_NUMBER=1
```

### 2. 启动自动化引擎

```bash
# 方式一: 直接启动（本地测试）
uv run python -m gh_nexus automation --port 8080

# 方式二: Docker部署后启动
docker-compose up -d
docker-compose exec app python -m gh_nexus automation --port 8080 --secret your_webhook_secret
```

### 3. 配置 GitHub Webhook

在 GitHub 仓库设置中添加 Webhook：

- **Payload URL**: `https://your-domain.com:8080/webhook`
- **Content type**: `application/json`
- **Events**: 
  - `Issues`
  - `Issue comment`
  - `Pull requests`

## 触发 Agent 的方式

### 方式一: 创建新 Issue
创建任何新 Issue 都会触发 Agent 分析和处理。

### 方式二: 给 Issue 添加标签
给 Issue 添加 `agent` 或 `auto` 标签，Agent 会自动处理。

### 方式三: 评论 `/agent`
在 Issue 评论中输入 `/agent` 命令，Agent 会开始处理。

## 工作流程

```
1. GitHub Issue 创建/标签/评论
        ↓
2. Webhook 接收事件
        ↓
3. AutomationEngine 解析 Issue
        ↓
4. 创建 Git Worktree (隔离工作区)
        ↓
5. 分配给 Worker Agent 执行
        ↓
6. Agent 完成 → 自动创建 PR
        ↓
7. 评论通知完成
```

## 可用命令

```bash
# 初始化
uv run python -m gh_nexus init

# 启动引擎
uv run python -m gh_nexus start -r "需求描述"

# 启动自动化模式（Webhook）
uv run python -m gh_nexus automation --port 8080

# 查看状态
uv run python -m gh_nexus status

# 运行测试
uv run python -m gh_nexus test

# 评估结果
uv run python -m gh_nexus evaluate
```

## 环境变量

| Variable | Description |
|----------|-------------|
| GITHUB_TOKEN | GitHub Personal Access Token |
| GITHUB_OWNER | GitHub organization/user |
| GITHUB_PROJECT_NUMBER | GitHub Project number |
| AGENT_WORKERS | 逗号分隔的agent列表 |
| LOG_LEVEL | 日志级别 |

## 角色定义

| Role | Function | Core Capabilities |
|------|----------|-------------------|
| Visionary | Define project goals | Requirements understanding, goal breakdown |
| Overseer | Monitor progress | Progress tracking, risk alerting |
| Interpreter | Analyze requirements | Requirements analysis, task breakdown |
| Dispatcher | Assign tasks | Task dispatch, load balancing |
| Worker | Execute code | Code generation, file operations |
| Tester | Write tests | Test coverage, validation |
| Rewarder | Evaluate results | Quality assessment, feedback |

## 开发

```bash
# 安装依赖
uv sync

# 运行测试
uv run pytest

# 代码检查
uv run ruff check .
```
