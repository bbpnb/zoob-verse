# zoob-verse — AI Agent 项目简报

> 这个文件是给 AI Agent 的仓库级入口。`PROJECT.md` 不是通用标准名，不同 agent 是否自动识别取决于各自实现；如果你的 agent 不认它，就把它当作手动入口文档。

## 当前定位

zoob-verse 是一个面向叙事文本的分层研究工作台，而不是单纯的“建图脚本”。

主线：

- LightRAG 负责抽取和召回
- `src/core/workbench.py` 负责归一化、报告和运行目录
- `runs/` 保存每次实验
- `events.json`、`facets.json`、`views/` 是实验性辅助层，用来把主图谱再整理成可研究的材料切片，不是主图谱本体，也不是最终结论
- 主图谱始终以 `graph.normalized.json` 为准

## 必须遵守

- 只用 `.env` 放本地密钥
- 变更模型和重跑大索引前先确认成本
- `index/eval/report/direct-analyze` 是主流程
- 索引模型、查询模型、embedding 版本都要记录

## 开发入口

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

常用命令：

```bash
python -m src jinyong index
python -m src jinyong query
python -m src jinyong eval
python -m src jinyong report
python -m src jinyong visualize
python -m src jinyong direct-analyze
```

## 相关文档

- `README.md`
- `ARCHITECTURE.md`
- `docs/decisions.md`
- `docs/plans/`
- `docs/research/`
- `.ai-skills/literary-knowledge-graph/SKILL.md`
