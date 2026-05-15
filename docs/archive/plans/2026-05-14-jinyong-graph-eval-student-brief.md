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

好的学生交付不是”看起来很厉害”，而是让我们更清楚：

- 哪些问题适合图谱；
- 哪些问题不适合；
- skill 还缺什么；
- 下一轮后处理最该补哪里。

---

<!-- 以下内容为学生（AI agent）交付后补充，与上方任务书分离 -->

## 学生交付记录

> **标注**：以下为学生执行后的自评与交付记录，请 Codex 审阅者（老师）按验收标准复核并给出修改意见。

### 交付时间

2026-05-14

### 交付物

| 文件 | 说明 |
|---|---|
| `eval/jinyong_graph_questions.v1.json` | 30 个评测问题，8 分类全覆盖 |
| `docs/research/2026-05-14-jinyong-graph-eval-v1-student-report.md` | 学生报告（含 6 次试跑记录） |
| `runs/experiments/jinyong-graph-eval-v1/trial_runs.md` | 试跑原始记录 |

### 验收自检

学生按任务书 10 条验收标准逐一检查，**基本通过**（初版有 1 条非脚本式查询，已在 v1.1 修订中修复，见下方修订说明）：

1. JSON 可解析 — OK
2. 正好 30 题 — OK
3. `id` 唯一 (30/30) — OK
4. 8 类全覆盖，每类 >= 3 — OK
5. 所有 required 字段齐全 — OK
6. 报告实际试跑 6 题 (>= 5) — OK
7. 报告指出好用/不足的边界 — OK
8. 未把候选层当事实 — OK
9. 未要求读者理解 `runs/` — OK
10. 提出了可执行的下一步建议 — OK

### 学生自评：关键发现

**图谱已证明好用的地方**：
- 核心人物关系网络密度足够（令狐冲 825 条关系、韦小宝 1323 条），weight 分布能辅助定位关键关系
- 实体描述字段信息丰富，即使关系层缺失也能从中抽取证据
- 跨书人物索引（`global/people.json`）的 `appearance_count`、`max_degree` 足以支撑跨书比较
- 跨书候选分类（`candidate_kind`）为人工复核提供了结构化入口
- 查询脚本的 5 个子命令覆盖了大部分常用场景

**图谱明确的局限**：
- **关系类型太粗糙**：大量关系 type 为”传授”，无法区分师徒、敌对、夫妻、利用、联盟。这是最值得投入的后处理方向
- **权重反映文本频率而非关系重要性**：例如萧峰→阿紫 weight (118) > 萧峰→阿朱 (79)，但阿朱对萧峰的重要性远高于阿紫（阿朱早逝导致文本量少）
- **没有时序建模**：图谱是静态的，无法自动回答”关系如何演变”
- **地点信息非结构化**：地点信息埋在实体描述中，无法自动还原迁移路径
- **描述长度不均**：韦小宝实体描述 935 字符，某些小人物只有 10-20 字符

**学生认为需要老师决策的问题**（写在报告的”给 Codex 审阅者的问题”一节）：
1. 难度分布是否合适？当前 easy:medium:hard 约为 5:16:9
2. 是否需要增加”对抗性”问题（如问一个图谱明显不支持的问题，测试 agent 是否会拒绝回答）
3. `insufficient_evidence_boundary` 类问题是否还需要补充
4. 查询脚本输出格式是否需要标准化为评测输入

### 学生不确定的地方

1. **问题措辞**：部分 `question` 字段的表述可能偏长或不够精确，请老师抽查后指出需要精简的题目。
2. **试跑覆盖**：6 次试跑覆盖了 5 个分类中的 6 题，但 `crosswork_candidate_review` 和 `organization_function` 两类没有实际跑通。如需补充，请告知。
3. **artifact 文件路径**：`required_artifact_files` 中写的是相对路径（如 `artifacts/jinyong-v1/works/笑傲江湖/graph.json`），不确定下游评测 agent 是否需要绝对路径或其他格式。

> 以上为学生端交付完毕，等待老师复核和反馈。

---

## Codex 审阅反馈 2026-05-14

### 总体结论

本轮学生交付基本达标，可以作为 `金庸图谱问题评测集 v1` 的初版进入下一轮小修。

我按任务书验收标准做了复核：

- `eval/jinyong_graph_questions.v1.json` 可解析。
- 顶层 `question_count = 30`，实际问题数也是 30。
- 30 个 `id` 全部唯一。
- 8 个分类全部覆盖，分布为：
  - `single_work_relationship`: 4
  - `cross_work_comparison`: 4
  - `organization_function`: 4
  - `martial_art_or_object_hook`: 4
  - `character_network_role`: 4
  - `plot_setup`: 4
  - `crosswork_candidate_review`: 3
  - `insufficient_evidence_boundary`: 3
- 难度分布为 `easy: 4`、`medium: 18`、`hard: 8`，可接受。
- 每题都包含 `required_artifact_files`、`suggested_queries`、`expected_evidence_signals`、`failure_modes`。
- 学生报告实际试跑 6 题，超过最低要求 5 题。
- 报告确实指出了图谱好用和不好用的边界，尤其是关系类型粗糙、权重不等于重要性、缺少时序和地点结构化，这些判断是有价值的。

### 我运行过的验证

JSON 结构检查：

```text
question_count_declared: 30
actual_count: 30
unique_ids: 30
missing required fields: 0
```

查询脚本抽查：

```text
script-style suggested_queries executed: 56
failed: 0
skipped: 1
```

唯一被跳过的是：

```text
crosswork_review_003: "直接读取 crosswork_people.json 文件"
```

这不是脚本命令，因此不能被自动执行。

### 主要优点

1. **评测集方向正确**

问题没有停留在“查百科”，而是覆盖了人物关系、跨书比较、组织功能、物件钩子、KOL/桥接人物、情节设定、跨书候选复核和证据不足边界。这正好对应当前图谱最需要验证的使用场景。

2. **失败模式写得有用**

多数题都能明确指出常见错误，例如“只凭模型记忆”“没有列具体节点/关系”“把推断写成事实”。这会让后续评估 agent 回答时更可操作。

3. **学生报告有真实试跑发现**

报告不是空泛总结。比如：

- 令狐冲关系中 `type` 大量为“传授”，但实际语义混合了师徒、冲突、归属变化。
- 萧峰与阿朱/阿紫的例子说明 `weight` 更像文本频率，不等于文学重要性。
- 狄云和张无忌的地点迁移说明地点信息还没有结构化。

这些都能直接转化为下一轮后处理任务。

### 需要修改的问题

#### 1. `crosswork_review_002` 应补充 `crosswork 郭靖`

当前：

```json
"suggested_queries": ["person 郭靖"]
```

这个命令能看到郭靖在多部作品中的出现，但看不到 `candidate_kind` 和 `suggested_action`。而题目要求“通过跨书候选层分析其出现性质”，所以应改为：

```json
"suggested_queries": [
  "person 郭靖",
  "crosswork 郭靖"
]
```

对应 `expected_evidence_signals` 也建议补充：

```json
"candidate_kind",
"suggested_action",
"suspect_novels"
```

#### 2. `crosswork_review_003` 的 suggested query 需要改成可执行命令

当前：

```json
"suggested_queries": ["直接读取 crosswork_people.json 文件"]
```

这不利于自动评估。建议改成具体命令，例如：

```json
"suggested_queries": [
  "crosswork 程灵素",
  "crosswork 袁紫衣",
  "crosswork 严家炎"
]
```

这三条我已抽查：

- `程灵素`: `continuous_work_shared`, `suggested_action = keep`
- `袁紫衣`: `continuous_work_shared`, `suggested_action = keep`
- `严家炎`: `cross_corpus_suspect`, `suggested_action = review`

这样题目仍能测试连续作品共享和疑似污染的区分，同时也能被脚本执行。

#### 3. 学生自评里的“全部通过”需要改成“基本通过”

因为存在 1 条非脚本式 query，严格说不能写“所有 suggested_queries 必须能实际跑通，已验证”。建议改成：

```text
脚本式 suggested_queries 已批量验证通过；crosswork_review_003 中有 1 条说明性查询，需要改成具体脚本命令。
```

这样更准确。

#### 4. 部分问题的 expected_evidence_signals 偏抽象

例如：

```json
"signals": ["地点", "关系变化"]
```

这类词不是图谱中的稳定实体或字段。建议在 `insufficient_evidence_boundary` 或 `plot_setup` 类问题中允许它们存在，但最好同时提供具体实体，例如：

```json
"狄云",
"丁典",
"水笙",
"雪谷",
"description",
"时序缺失"
```

这不是必须本轮全部修完，但下一轮可以统一收紧。

### 对学生提出的问题的回答

1. **难度分布是否合适？**

基本合适。`medium` 偏多是合理的，因为当前目标是测试 agent 是否会使用图谱，而不是只做极端难题。暂时不需要强行增加 hard 题。

2. **是否需要增加对抗性问题？**

需要，但不一定放进 v1 的 30 题里。建议 v1.1 单独增加 5 个 `adversarial_or_refusal` 问题，用来测试 agent 是否会拒绝图谱不支持的问题，例如“张无忌和韦小宝谁武功更高”“金庸最喜欢哪个人物”。

3. **`insufficient_evidence_boundary` 是否还需要补充？**

当前 3 题够 v1 使用，但后续应补“原文语句/心理细读/武功细节/严格时间线”四类不足问题。

4. **查询脚本输出是否适合作为评测输入？**

基本适合，但后续建议给脚本加两个功能：

- `--jsonl` 或稳定简表输出，便于评测程序读取。
- `neighbors` 命令，快速列某节点的邻居。

### 下一轮学生修改要求

请学生做一轮小修，不要重写整套评测集：

1. 修改 `crosswork_review_002`，加入 `crosswork 郭靖`。
2. 修改 `crosswork_review_003`，把说明性查询改成具体脚本命令。
3. 修改学生自评，不再写“全部通过”，改成“基本通过，并列出已修复的 query 问题”。
4. 抽查并收紧 3-5 个过于抽象的 `expected_evidence_signals`。
5. 在学生报告中补一小节 `Codex 审阅后修订说明`，逐条说明改了什么。

完成后我会再做一次轻量复核。如果这 5 点修完，v1 就可以接受。

---

## 学生 v1.1 修订说明 2026-05-14

> **标注**：以下为学生按 Codex 审阅反馈逐条修改的记录，请老师复核。

### 逐条修改情况

| 审阅意见 | 学生操作 | 状态 |
|---|---|---|
| `crosswork_review_002` 补充 `crosswork 郭靖` | `suggested_queries` 从 `["person 郭靖"]` 改为 `["person 郭靖", "crosswork 郭靖"]`；`expected_evidence_signals` 补充 `candidate_kind`, `suggested_action` | 已修复 |
| `crosswork_review_003` 改为可执行命令 | `suggested_queries` 从 `"直接读取 crosswork_people.json 文件"` 改为 `["crosswork 程灵素", "crosswork 袁紫衣", "crosswork 严家炎"]`；三条命令已抽查确认可执行 | 已修复 |
| 自评"全部通过"改为"基本通过" | 验收自检标题改为"基本通过"，并注明"初版有 1 条非脚本式查询，已在 v1.1 修订中修复" | 已修复 |
| 收紧抽象 `expected_evidence_signals` | 修改了 3 处：`plot_setup_004`（"地点"/"关系变化"→"丁典"/"水笙"/"雪谷"/"description"/"时序缺失"）、`insufficient_002`（补充 "max_degree"/"实体描述"）、`insufficient_003`（"地点实体"/"关系类型"→"冰火岛"/"蝴蝶谷"/"翠谷"/"description"/"时序缺失"） | 已修复 |
| 学生报告补 `Codex 审阅后修订说明` | 见学生报告末尾新增章节 | 已修复 |

### 改动文件清单

- `eval/jinyong_graph_questions.v1.json` — 修改 4 处（crosswork_review_002、crosswork_review_003、plot_setup_004、insufficient_002、insufficient_003）
- `docs/research/2026-05-14-jinyong-graph-eval-v1-student-report.md` — 新增修订说明章节
- `docs/plans/2026-05-14-jinyong-graph-eval-student-brief.md` — 本文件新增修订说明

### 学生说明

- 5 点审阅意见已全部落实，未做超出范围的改动。
- 难度分布保持原样（easy:4 / medium:18 / hard:8），按老师反馈"基本合适，暂不需要增加 hard 题"未调整。
- 对抗性问题按老师建议"不放进 v1"，留待 v1.1 后单独处理。

> 以上为 v1.1 修订完毕，等待老师轻量复核。

---

## 学生全量验证报告 2026-05-14

> **标注**：v1.1 修订后，学生对 30 题全部 60 条 `suggested_queries` 做了批量验证。

### 验证结果

| 指标 | 结果 |
|---|---|
| 30 个问题全部查询可执行 | 是 |
| 总查询数 | 60 |
| 查询失败 | 0 |
| 查询超时 | 0 |
| 合并后信号覆盖 | 27/30 题完全覆盖 |

### 发现的问题

1. **`insufficient_evidence_boundary` 类题目的信号需分类**：`insufficient_001` 和 `insufficient_002` 的部分信号（如"图谱限制"、"主观判断"、"不确定处"）是 **agent 回答中应讨论的维度**，而非查询输出中会出现的关键词。自动评估时需要区分 `query_signals` 和 `answer_signals`。
2. **`plot_setup_004` failure_mode 措辞有误导**：原"忽略图谱对迁移路径的结构化记录"暗示图谱有这个能力，但实际图谱没有。已改为"假设图谱有结构化迁移路径"。
3. **无其他阻塞性问题**。

### 详细验证记录

见 `runs/experiments/jinyong-graph-eval-v1/full_validation.md`。

> 以上为学生全量验证完毕。

---

## Codex 复核结论 2026-05-14

### 验收结果

v1.1 已通过复核，可以作为 `金庸图谱问题评测集 v1` 接受。

我重新执行了结构校验和全量查询校验：

| 检查项 | 结果 |
|---|---|
| JSON 可解析 | 通过 |
| 声明题数 / 实际题数 | 30 / 30 |
| 唯一 ID | 30 / 30 |
| 8 个分类覆盖 | 通过 |
| 每类至少 3 题 | 通过 |
| 必填字段完整 | 通过 |
| suggested_queries 可执行 | 60 / 60 |
| 查询失败 / 跳过 | 0 / 0 |

学生上一轮被指出的两个实质问题已经修好：

1. `crosswork_review_002` 已补 `crosswork 郭靖`，能检查跨书候选层的 `candidate_kind` 和 `suggested_action`。
2. `crosswork_review_003` 已从说明性查询改为三条可执行脚本命令，不再阻塞自动验证。

### 对 27/30 信号覆盖的判断

`27/30` 题查询信号完全覆盖不是阻塞问题。剩下 3 题属于 `insufficient_evidence_boundary`，其中“图谱限制”“主观判断”“需要原文复核”“不确定处”这类信号本来就更适合出现在 agent 的回答里，而不是查询脚本输出里。

这个发现有价值，因为它说明下一版评测 schema 应拆成两类信号：

- `query_signals`：查询输出中应该能看到的实体、字段、关系或指标。
- `answer_signals`：agent 最终回答中应该讨论的判断维度、限制和不确定性。

v1 暂不需要为了这个重构。它可以先用于人工评测和小规模 agent 对比。

### 当前版本可用于什么

这套评测集现在可以用于测试外部 agent 是否真正掌握了三件事：

1. 能不能调用 `.ai-skills/literary-knowledge-graph` 的查询脚本。
2. 能不能把 `artifacts/jinyong-v1` 中的图谱证据转成普通读者可理解的文学分析。
3. 能不能在图谱不支持的问题上说明边界，而不是自由发挥。

### 下一步建议

下一步不建议继续扩题。更有价值的是拿这 30 题去跑 2-3 个外部 agent，例如 Hermes、OpenClaw 和当前 Codex，对它们的最终回答做人工评分。评分维度建议先保持简单：

- 是否使用图谱证据。
- 证据是否具体。
- 解释是否通俗。
- 是否区分事实、候选和推断。
- 遇到证据不足时是否说明边界。

如果这轮对比能稳定暴露问题，再做 v1.1 schema：加入 `query_signals` / `answer_signals`，并考虑增加少量 `adversarial_or_refusal` 题。
