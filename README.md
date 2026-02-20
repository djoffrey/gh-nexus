# Gh Nexus - AI Agent Project Orchestration System

以GitHub Project为中心，使用gh命令管理，将注册的agent作为worker的自动化开发系统。

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Project                              │
│              (Task Board via gh CLI)                            │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ gh commands
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Core Engine                                   │
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
│                    Agent Workers                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │  opencode  │ │claude code│ │   cursor   │ │  windsurf  │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 角色定义

| Role | Function | Core Capabilities |
|------|----------|-------------------|
| Visionary | Define project goals & direction | Requirements understanding, goal breakdown |
| Overseer | Monitor progress, assess risks | Progress tracking, risk alerting |
| Interpreter | Analyze requirements, decompose tasks | Requirements analysis, task breakdown |
| Dispatcher | Assign tasks to workers | Task dispatch, load balancing |
| Worker | Execute code tasks | Code generation, file operations |
| Tester | Write and run tests | Test coverage, validation |
| Rewarder | Evaluate results, suggest improvements | Quality assessment, feedback optimization |

## 快速开始

```bash
# 1. 配置环境
cp .env.example .env
# 编辑 .env 填写 GITHUB_TOKEN 等配置

# 2. 启动开发环境
docker-compose up -d

# 3. 进入容器
docker-compose exec app bash

# 4. 初始化项目
python -m gh_nexus init

# 5. 启动系统
python -m gh_nexus start
```

## 环境变量

| Variable | Description |
|----------|-------------|
| GITHUB_TOKEN | GitHub Personal Access Token |
| GITHUB_OWNER | GitHub organization/user |
| GITHUB_PROJECT_NUMBER | GitHub Project number |
| OPENCODE_API_KEY | OpenCode API key (可选) |
| ANTHROPIC_API_KEY | Anthropic Claude API key (可选) |
| OPENAI_API_KEY | OpenAI API key (可选) |
