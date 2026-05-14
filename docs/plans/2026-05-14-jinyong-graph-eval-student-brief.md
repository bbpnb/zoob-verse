# 金庸图谱评测集 v1 学生任务书

## 任务背景

当前项目已经形成三层结构：

- 研究层：`runs/`、`docs/research/`、`docs/plans/`、`WORKFLOWS.md`
- 成果层：`artifacts/jinyong-v1/`
- 能力封装层：`.ai-skills/literary-knowledge-graph/`

本任务的目标不是继续堆新图谱，也不是重跑大模型，而是检验当前成果是否真的能被外部 agent 用来做“有证据边界的文学分析”。

你是执行学生。请按本文档完成研究、试跑和总结。Codex 会作为审阅者，在你交付后按验收标准复核，并在同一文档或新反馈文档中给出修改意见。若某些问题你解决不了，先记录原因和你尝试过的方法，不要硬编结论。

## 总目标

构建一个小而清晰的“金庸图谱问题评测集 v1”，用于测试不同 agent 是否真正使用了 `artifacts/jinyong-v1` 和 `.ai-skills/literary-knowledge-graph`。

评测集应能回答三件事：

1. Agent 是否会调用图谱数据，而不是只凭模型记忆。
2. Agent 是否能把图谱证据写成普通读者能懂的分析。
3. 当前图谱和 skill 在哪些问题类型上好用，哪些地方还缺后处理或数据结构。

## 边界

本轮不要做：

- 不要重跑金庸全集图谱。
- 不要调用付费 LLM API，除非用户明确批准。
- 不要修改 `artifacts/jinyong-v1` 的原始数据。
- 不要大改 `.ai-skills/literary-knowledge-graph`，除非发现明确 bug。
- 不要把 `runs/` 里的实验 run 当作默认使用入口。

本轮可以做：

- 使用 `artifacts/jinyong-v1`。
- 使用 `.ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py`。
- 新增评测数据、评测报告、试跑记录。
- 提出后续需要 Codex 或用户决策的改进建议。

## 必读入口

先读：

1. `artifacts/jinyong-v1/README.md`
2. `artifacts/jinyong-v1/examples/query_playbook.md`
3. `artifacts/jinyong-v1/examples/sample_answers.md`
4. `.ai-skills/literary-knowledge-graph/SKILL.md`
5. `docs/narrative/jinyong-kg-project-retrospective.md`

不要一开始读完整 `runs/`。

## 建议使用命令

先做自检：

```bash
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py check
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py summary
```

常用查询：

```bash
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py person 洪七公
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py top-people --exclude-main --top 30
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py relations --work 鹿鼎记 --name 韦小宝 --top 12
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py search --work 笑傲江湖 --q 辟邪剑谱 --top 20
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py crosswork 韦小宝
```

## 交付物

请新增以下文件：

```text
eval/jinyong_graph_questions.v1.json
docs/research/2026-05-14-jinyong-graph-eval-v1-student-report.md
```

如果需要保存少量试跑输出，可以新增：

```text
runs/experiments/jinyong-graph-eval-v1/
```

但不要把大型临时输出、完整大 JSON 拷贝进去。

## 评测集格式

`eval/jinyong_graph_questions.v1.json` 应为 JSON，顶层结构：

```json
{
  "version": "jinyong_graph_questions_v1",
  "purpose": "Evaluate whether agents can use artifacts/jinyong-v1 for evidence-grounded literary analysis.",
  "question_count": 30,
  "questions": [
    {
      "id": "single_relation_001",
      "category": "single_work_relationship",
      "difficulty": "medium",
      "question": "通过图谱分析《笑傲江湖》中令狐冲与岳不群为什么不是简单的师徒决裂。",
      "required_artifact_files": [
        "artifacts/jinyong-v1/works/笑傲江湖/graph.json"
      ],
      "suggested_queries": [
        "relations --work 笑傲江湖 --name 令狐冲 --top 12",
        "relations --work 笑傲江湖 --name 岳不群 --top 12"
      ],
      "expected_evidence_signals": [
        "令狐冲",
        "岳不群",
        "风清扬",
        "任我行",
        "华山派"
      ],
      "answer_should_include": [
        "简短结论",
        "图谱证据",
        "基于证据的解释",
        "不确定处"
      ],
      "failure_modes": [
        "只凭模型记忆讲伪君子",
        "没有列出具体节点或关系",
        "把推断写成确定事实"
      ]
    }
  ]
}
```

字段要求：

- `id` 唯一。
- `category` 使用下文分类之一。
- `difficulty` 可为 `easy`、`medium`、`hard`。
- `required_artifact_files` 写主要依赖文件，不需要列所有文件。
- `suggested_queries` 写给 agent 的查询方向，不要求一定完全复制命令前缀。
- `expected_evidence_signals` 写应出现的实体、关系、指标或候选层字段。
- `failure_modes` 写常见错误，便于后续自动/人工评估。

## 问题分类

请做 30 个问题，覆盖以下类型。每类至少 3 个。

1. `single_work_relationship`：单书人物关系分析。
2. `cross_work_comparison`：跨作品人物或主题比较。
3. `organization_function`：门派、帮会、朝廷、秘密组织的叙事功能。
4. `martial_art_or_object_hook`：武功、秘籍、兵器、宝物如何推动情节。
5. `character_network_role`：非主角 KOL、中介人物、桥接人物。
6. `plot_setup`：吸引读者的情节设定和叙事机制。
7. `crosswork_candidate_review`：跨书人物候选是真引用、连续作品共享还是疑似污染。
8. `insufficient_evidence_boundary`：图谱证据不足，应要求原文复核的问题。

可参考问题：

- 通过图谱找两个不是主角但能算 KOL 的人物，并说明证据。
- 通过图谱列两个经典的吸引读者的情节设定。
- 分析韦小宝如何同时连接皇权、天地会、吴三桂和神龙教。
- 比较郭靖、杨过、张无忌的跨书出现方式。
- 少林、武当、丐帮在不同作品里更像权力机构、道德象征，还是剧情连接器？
- 辟邪剑谱、屠龙刀、连城诀这类物件为什么容易成为故事发动机？
- 韦小宝出现在多部非《鹿鼎记》作品里，应如何判断真实引用和疑似污染？
- 哪些问题当前图谱不能可靠回答？为什么？

## 学生报告要求

请在 `docs/research/2026-05-14-jinyong-graph-eval-v1-student-report.md` 写报告，结构如下：

```markdown
# 金庸图谱评测集 v1 学生报告

## 执行摘要

## 产物清单

## 评测集设计原则

## 分类覆盖情况

## 试跑结果

至少选择 5 个问题，用 skill 和查询脚本实际试跑，并写出：
- 使用了哪些命令
- 拿到了哪些关键证据
- 草拟答案摘要
- 发现了什么问题

## 当前图谱好用的地方

## 当前图谱不足的地方

## 对 skill 的改进建议

## 对后处理的改进建议

## 给 Codex 审阅者的问题
```

报告要具体。不要只写“效果不错”。应给出证据和例子。

## 验收标准

Codex 审阅时会检查：

1. JSON 是否可解析。
2. 是否正好 30 个问题。
3. `id` 是否唯一。
4. 8 个分类是否都覆盖，且每类至少 3 个。
5. 每个问题是否包含 `required_artifact_files`、`suggested_queries`、`expected_evidence_signals`、`failure_modes`。
6. 报告是否实际试跑至少 5 个问题。
7. 报告是否指出图谱好用和不好用的边界。
8. 是否避免把候选层当成事实。
9. 是否避免要求用户理解 `runs/` 或施工文档。
10. 是否提出可执行的下一步建议。

## 协作流程

学生完成后，请把结果提交或至少保存在上述文件中。

Codex 审阅者会：

1. 运行 JSON 校验。
2. 抽查若干题的 suggested queries。
3. 对报告给出 review。
4. 如果问题清楚但实现粗糙，给出修改意见让学生再改。
5. 如果学生多轮仍无法解决，Codex 再亲自接手修复。

## 注意

这不是考试，也不是为了证明某个 agent 更强。目标是让项目变得更可靠、更能被外部 agent 使用。

好的学生交付不是“看起来很厉害”，而是让我们更清楚：

- 哪些问题适合图谱；
- 哪些问题不适合；
- skill 还缺什么；
- 下一轮后处理最该补哪里。
