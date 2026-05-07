# zoob-verse

叙事文本知识图谱研究工作台。

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# 编辑 .env，填入需要的 provider key

python -m src --help
python -m src jinyong --help
```

## 主流程

```bash
# 构建索引
python -m src jinyong index \
  --novel src/modules/jinyong/data/raw/越女剑.txt \
  --corpus 越女剑 \
  --model deepseek-v4-flash \
  --run-name smoke

# 查询与报告
python -m src jinyong eval --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke
python -m src jinyong report --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke

# 可选：从规范化图谱生成实验性辅助层
python -m src jinyong normalize-graph --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke
python -m src jinyong extract-events --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke
python -m src jinyong tag-facets --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke --profile jinyong
python -m src jinyong derive-view --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke --facet 女性角色

# 长上下文对照
python -m src jinyong direct-analyze \
  --novel src/modules/jinyong/data/raw/越女剑.txt \
  --question "阿青的剑术源头和人物动机有什么冷门解读？"
```

## 文档入口

- [WORKFLOWS.md](WORKFLOWS.md)
- [PROJECT.md](PROJECT.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/decisions.md](docs/decisions.md)
- [docs/plans/](docs/plans/)
- [docs/research/](docs/research/)
- [.ai-skills/literary-knowledge-graph/SKILL.md](.ai-skills/literary-knowledge-graph/SKILL.md)

## 约定

- API Key 只通过 `.env` 提供，不提交明文。
- `runs/` 保存标准实验输出。
- 旧的一次性脚本已弃用，后续实验优先走 CLI。
- `events.json`、`facets.json`、`views/` 是从 `graph.normalized.json` 派生出的研究材料，不是主图谱本体。
