# 金庸图谱 Start Here

如果你是第一次接手这个项目，无论你是人还是 AI agent，都不要先扫整个 `runs/jinyong/`。  
当前更合理的入口是：

1. [`runs/jinyong/_global/manifest.json`](../runs/jinyong/_global/manifest.json)
2. [`runs/jinyong/_global/scorecard.json`](../runs/jinyong/_global/scorecard.json)
3. [`runs/jinyong/_global/canonical_runs.json`](../runs/jinyong/_global/canonical_runs.json)
4. [`runs/jinyong/_global/global_people.index.json`](../runs/jinyong/_global/global_people.index.json)
5. [`WORKFLOWS.md`](../WORKFLOWS.md)

## 这个项目现在是什么

当前项目已经完成金庸全集 `15` 部作品的代表性主 run，并在此基础上做了 corpus 级后处理。

当前 corpus 主规模：

- 作品数：`15`
- 总节点数：`30621`
- 总边数：`47052`
- 总 token：`28705757`

它现在更适合被理解为：

- 可用的文学图谱研究工作台
- 可审计的单书查询与跨书人物索引底座
- 可继续做后处理、实体对齐、研究验证的中间层

它还不是：

- 终局知识库
- 全自动可靠的跨书实体系统
- 不经复核即可直接下结论的百科事实源

## 先看哪些文件

| 文件 | 角色 | 用途 |
| --- | --- | --- |
| `runs/jinyong/_global/manifest.json` | 机器入口 | 给其他 agent 的主入口，说明当前 corpus 该怎么看 |
| `runs/jinyong/_global/scorecard.json` | 事实层 | corpus 总规模、每部作品主 run 的结构摘要 |
| `runs/jinyong/_global/canonical_runs.json` | 事实层 | 每部作品默认应使用的权威 `run_dir` |
| `runs/jinyong/_global/global_people.index.json` | 事实层 | 当前跨作品人物入口，带 `home_novel_guess`、出现作品、局部结构信号 |
| `runs/jinyong/_global/global_people.crosswork_candidates.json` | 候选层 | 跨书人物候选分类，如连续作品共享、疑似污染、待复核 |
| `runs/jinyong/_global/global_people.survivor_audit.json` | 审计层 | 带称谓信号但仍被保留的人物，供人工复核 |
| `runs/jinyong/_global/global_people.excluded_role_like.json` | 审计层 | 被排除出主人物层的泛称、称谓、角色标签 |
| `runs/jinyong/_global/noise_candidates.*` | 候选/审计层 | 全集实体与关系噪声候选，不是最终清洗结果 |

## 安全使用顺序

### 1. 单书问题

如果你要回答某一部作品的问题：

1. 先查 `canonical_runs.json` 找到该作品的 `run_dir`
2. 再进入该 `run_dir` 看：
   - `graph.normalized.json`
   - `report.md|json`
   - `queries.json`
   - `subgraphs/`
3. 需要继续提问时，再用 `python -m src jinyong query ...`

不要用“最新 run”猜主结果。  
单书默认入口永远是 `canonical_runs.json`。

### 2. 跨书人物问题

如果你要回答“某个人出现在哪些作品里”“某个人是否可能存在跨书污染”这类问题：

1. 先查 `global_people.index.json`
2. 再查 `global_people.crosswork_candidates.json`
3. 必要时再看 `survivor_audit` 或 `excluded_role_like`

推荐理解方式：

- `global_people.index.json`：当前可默认使用的人物层
- `crosswork_candidates`：需要分类判断的跨书候选
- `survivor_audit`：仍保留但值得多看一眼的称谓化人物

### 3. 长篇阅读与验证

对长篇不要先盯整图 `graph.html`。  
更有效的顺序是：

1. `report`
2. `queries`
3. `subgraphs/`
4. 必要时再看 `graph.normalized.json`

## 产物分层

为了避免误用，当前 `_global` 的主要产物应该按三层理解：

### `fact_like`

这些可以作为当前默认入口：

- `scorecard.json`
- `canonical_runs.json`
- `global_people.index.json`

### `candidate_like`

这些表示“有价值的候选”，不是最终事实：

- `global_people.crosswork_candidates.json`
- `noise_candidates.entities.json`
- `noise_candidates.relations.json`

### `audit_like`

这些表示“需要审计或解释的边界层”：

- `global_people.survivor_audit.json`
- `global_people.excluded_role_like.json`
- `noise_candidates.summary.json`

## 不要默认假设

1. 同名人物一定是同一人
2. 跨书出现一定代表真实共享实体
3. 候选层等于事实层
4. 单书全图 HTML 适合作为长篇主界面
5. 所有后处理都已经完成

## 如果你要继续建设

当前最适合继续做的，不是再盲目加新图，而是：

1. 关系归一
2. 组织/门派层
3. 实体对齐
4. 面向研究问题的主题视图
5. 证据化查询验证

## 延伸文档

- [`docs/research/2026-05-12-jinyong-corpus-handoff.md`](./research/2026-05-12-jinyong-corpus-handoff.md)
- [`docs/research/2026-05-12-jinyong-global-people-layer-handoff.md`](./research/2026-05-12-jinyong-global-people-layer-handoff.md)
- [`docs/research/2026-05-12-jinyong-runs-retention-policy.md`](./research/2026-05-12-jinyong-runs-retention-policy.md)
- [`docs/research/2026-05-12-postprocessing-roadmap.md`](./research/2026-05-12-postprocessing-roadmap.md)
- [`WORKFLOWS.md`](../WORKFLOWS.md)
