---
name: literary-knowledge-graph
description: 从文学作品构建知识图谱 — 关系挖掘、模式发现、内容生成。支持金庸、古龙、刘慈欣等作品模块。
version: 0.1.0
author: graph-lore project
license: MIT
metadata:
  hermes:
    tags: [knowledge-graph, literary-analysis, graphrag, text-mining, neo4j]
    category: research
---

# Literary Knowledge Graph Platform

从叙事文本（文学作品、影视、诗歌等）中构建知识图谱，挖掘隐藏关系，发现模式，生成洞察。

## 项目路径

```
/Users/zhenboyuan/code/mine/graph-lore/
```

## 可用模块

| 模块 | 描述 | 实体类型 |
|------|------|---------|
| `jinyong` | 金庸武侠宇宙 | 人物、门派、武功、地点、事件 |
| `gulong` | 古龙武侠宇宙 | 人物、组织、兵器、流派、地点 |
| `liucixin` | 刘慈欣科幻宇宙 | 人物、科技、文明、事件、时间线 |

## CLI 参考

```bash
# 数据导入
python -m src <module> ingest --xlsx <xlsx路径>
python -m src <module> ingest --files <txt文件...>

# 图谱索引
python -m src <module> index --novel <txt路径>

# 查询
python -m src <module> query "<问题>"
python -m src <module> query --type reasoning "<推理问题>"

# 分析
python -m src <module> analyze --type shortest-path --from <A> --to <B>
python -m src <module> analyze --type community-detection
python -m src <module> analyze --type centrality --method betweenness
```

## 新增模块

1. 复制 `src/modules/jinyong/` 为新模块目录
2. 编辑 `config/settings.yaml` 定义实体/关系类型
3. 实现 `extract()` 和 `analyze()` 方法
4. CLI 自动发现新模块

## 架构

- **核心引擎**：通用图构建和分析（NetworkX）
- **模块系统**：各作品独立定义 schema 和处理逻辑
- **CLI 接口**：统一入口，动态分发到模块

详见 `ARCHITECTURE.md` 和 `docs/decisions.md`。

## Pitfalls

- **不要假设所有模块处理方式相同** — 金庸、唐诗、美剧的实体类型和分析目标完全不同
- **核心引擎保持通用** — engine.py 不关心任何具体实体类型
- **模块配置独立** — 每个模块有自己的 config/settings.yaml
- **Skill 不包代码** — Skill 记录方法论，代码在项目中
