# zoob-verse — AI Agent 项目简报

## 项目目标

从叙事文本（文学作品、影视、诗歌等）中构建知识图谱，挖掘隐藏关系，发现模式，生成洞察。

## ⚠️ 环境要求（所有 AI Agent 必读）

**本项目是 Python 项目，必须使用虚拟环境（venv）管理依赖，严禁安装到系统 Python！**

```bash
# 每次开发/运行前必须执行：
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 架构：Framework + Plugin

- **核心引擎**（`src/core/`）：通用图构建和分析，不关心任何具体实体类型
- **模块系统**（`src/modules/`）：每个作品（金庸、古龙、刘慈欣...）独立定义实体/关系类型、提取逻辑、分析方法
- **CLI 入口**：`python -m src <module> <command>`

## 关键设计原则

1. **核心引擎保持通用** — `engine.py` 只处理节点和边，不关心实体类型
2. **各模块完全独立** — 金庸、唐诗、美剧的实体类型和分析目标完全不同，不能假设一套接口
3. **CLI 是唯一对外接口** — Skill 和外部调用只需知道如何执行 CLI 命令
4. **Skill 不包代码** — `.ai-skills/` 记录方法论，代码在 `src/` 中

## CLI 命令

```bash
python -m src <module> ingest --xlsx <路径>      # 导入数据
python -m src <module> index --novel <路径>      # 构建索引
python -m src <module> query "<问题>"            # 查询
python -m src <module> analyze --type <方法>     # 分析
```

## 新增模块

1. 复制 `src/modules/jinyong/` 为新模块目录
2. 编辑 `config/settings.yaml` 定义实体/关系类型
3. 实现 `extract()` 和 `analyze()` 方法
4. CLI 自动发现新模块

## 技术栈

- Click（CLI）
- NetworkX（图计算）
- YAML（配置）
- LightRAG / GraphRAG（图谱构建，可选）
- Neo4j（图数据库，可选）

## 详细文档

- `README.md` — 快速开始
- `ARCHITECTURE.md` — 架构设计
- `docs/decisions.md` — 关键决策记录
- `docs/notes.md` — 踩坑记录和待办
- `.ai-skills/literary-knowledge-graph/SKILL.md` — 方法论 Skill
