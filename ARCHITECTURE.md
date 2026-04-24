# Architecture

## 设计理念

graph-lore 采用 **Framework + Plugin** 架构，核心思想：
- **核心引擎通用**：图构建、图分析、LLM 调用等通用能力与具体作品无关
- **各模块完全独立**：每个作品模块定义自己的实体/关系类型、提取逻辑、分析方法
- **CLI 统一入口**：`python -m src <module> <command>` 分发到具体模块

## 为什么不是分散项目？

最初考虑过为每个作品创建独立项目（jinyong-research、gulong-research...），但存在以下问题：
- 核心代码重复（图引擎、CLI 框架、LLM 调用）
- 依赖管理分散（每个项目一个 pyproject.toml）
- 跨作品分析困难（数据分散在不同项目中）
- Skill 管理复杂（方法论与具体项目绑定）

统一平台方案解决了这些问题：核心代码一份，新增作品只需加一个模块目录。

## 为什么各模块不能共享同一套 schema？

不同作品/内容的"研究维度"完全不同：
- **金庸武侠**：人物、门派、武功、地点 → 关系挖掘、地理映射
- **唐诗**：诗人、意象、格律、韵部 → 韵律统计、意象网络
- **美剧**：角色、剧情线、主题 → 角色弧光、剧情结构

这些不是"配置不同"就能解决的，提取逻辑、分析方法、输出形式都不同。因此每个模块独立实现 `extract()` 和 `analyze()`。

## 目录结构

```
graph-lore/
├── src/
│   ├── cli.py                     ← CLI 入口（动态发现模块）
│   ├── core/                      ← 通用核心引擎
│   │   ├── engine.py              ← 图构建/分析（NetworkX）
│   │   └── ...                    ← 未来：LLM 调用封装、查询引擎
│   └── modules/                   ← 各作品模块（插件式）
│       ├── base.py                ← 模块基类（定义接口）
│       ├── jinyong/               ← 金庸模块
│       │   ├── __init__.py        ← 模块实现
│       │   └── config/
│       │       └── settings.yaml  ← 金庸特定配置
│       ├── gulong/                ← 古龙模块
│       └── liucixin/              ← 刘慈欣模块
├── .ai-skills/                    ← AI Agent Skill
├── docs/                          ← 文档
├── data/                          ← 数据
└── pyproject.toml
```

## CLI 设计

CLI 是项目的唯一对外接口，Skill 只需知道如何调用 CLI：

```bash
# 数据导入
python -m src <module> ingest --xlsx data.xlsx
python -m src <module> ingest --files novel1.txt novel2.txt

# 图谱索引
python -m src <module> index --novel novel.txt

# 查询
python -m src <module> query "问题"
python -m src <module> query --type reasoning "推理问题"

# 分析
python -m src <module> analyze --type shortest-path --from A --to B
python -m src <module> analyze --type community-detection
python -m src <module> analyze --type centrality --method betweenness
```

## 模块接口

每个模块继承 `ModuleBase`，实现以下接口：

```python
class ModuleBase(ABC):
    name: str                      # 模块名称
    description: str               # 模块描述

    def get_entity_types() -> list[str]        # 实体类型
    def get_relationship_types() -> list[str]  # 关系类型
    def extract(text: str) -> (entities, rels) # 实体/关系提取
    def analyze(graph, method, **kwargs)       # 模块特定分析
    def get_cli() -> click.Group               # CLI 命令组
```

## Skill 与项目的关系

- **Skill**（`.ai-skills/`）：记录方法论、流程、注意事项、CLI 用法
- **项目**（`src/`）：存放可执行代码、配置、数据
- Skill 不依赖具体模块，只描述平台如何使用
- 各模块的配置差异通过 `config/settings.yaml` 管理

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| CLI | Click | 命令分组、动态模块发现 |
| 图计算 | NetworkX | 原型阶段，轻量无依赖 |
| 图数据库 | Neo4j（可选） | 生产级，持久化存储 |
| 图谱构建 | LightRAG / GraphRAG | LLM 自动提取实体和关系 |
| 配置 | YAML | 模块配置、实体类型定义 |
| 包管理 | hatch / pyproject.toml | 标准 Python 项目管理 |
