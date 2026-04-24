# graph-lore

**Literary Knowledge Graph Platform** — 从文学作品（及其他叙事文本）中构建知识图谱，挖掘隐藏关系，发现模式，生成洞察。

## 概览

graph-lore 是一个 **Framework + Plugin** 架构的知识图谱平台：
- **核心引擎**：通用的图构建、图分析、查询能力
- **模块系统**：每个作品（金庸、古龙、刘慈欣...）独立定义自己的实体类型、关系类型、提取逻辑和分析方法
- **CLI 接口**：统一的命令行入口，分发到具体模块

## 快速开始

```bash
# 安装
cd /Users/zhenboyuan/code/mine/graph-lore
pip install -e ".[dev]"

# 查看帮助
python -m src --help

# 金庸模块
python -m src jinyong ingest --xlsx data/金庸武侠世界.xlsx
python -m src jinyong index
python -m src jinyong query "郭靖在哪里初识黄蓉？"
python -m src jinyong analyze --type shortest-path --from 郭靖 --to 萧峰
```

## 可用模块

| 模块 | 描述 | 实体类型 |
|------|------|---------|
| `jinyong` | 金庸武侠宇宙 | 人物、门派、武功、地点、事件 |
| `gulong` | 古龙武侠宇宙 | 人物、组织、兵器、流派、地点 |
| `liucixin` | 刘慈欣科幻宇宙 | 人物、科技、文明、事件、时间线 |

## 新增模块

1. 复制 `src/modules/jinyong/` 为新模块目录
2. 编辑 `config/settings.yaml` 定义实体/关系类型
3. 实现 `extract()` 和 `analyze()` 方法
4. CLI 自动发现新模块

## 项目结构

```
graph-lore/
├── .ai-skills/                    ← AI Agent Skill（方法论）
├── src/
│   ├── cli.py                     ← CLI 入口
│   ├── core/                      ← 通用核心引擎
│   │   └── engine.py              ← 图构建/分析
│   └── modules/                   ← 各作品模块
│       ├── base.py                ← 模块基类
│       ├── jinyong/               ← 金庸
│       ├── gulong/                ← 古龙
│       └── liucixin/              ← 刘慈欣
├── config/                        ← 全局配置
├── data/                          ← 数据目录
├── docs/                          ← 文档
├── notebooks/                     ← 探索性分析
├── scripts/                       ← 运行脚本
├── tests/                         ← 测试
└── pyproject.toml
```

## 架构设计

详见 [ARCHITECTURE.md](ARCHITECTURE.md)

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check src/
```
