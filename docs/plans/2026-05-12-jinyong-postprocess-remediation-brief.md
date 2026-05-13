# 金庸后处理第一阶段整改任务书

> 用途：把当前 review 意见转成可直接交给其他 AI agent 的实施需求。  
> 注意：这是整改任务书，不是讨论稿。

## 目标

修复当前 `jinyong postprocess` 的关键缺陷，使其产物真正满足：

1. 只扫描 15 部 canonical 主结果
2. 正确生成 scorecard
3. 生成可解释的实体/关系噪声候选
4. 为下一阶段实体对齐和关系归一提供可靠输入

## 当前问题结论

当前版本**不能验收通过**。  
核心不是“没生成文件”，而是“生成了，但主输入选错了，规则也不够对”。

## 必改问题

### 1. 主 run 选择错误

**严重级别：高**

当前 `src/modules/jinyong/postprocess.py:32-84` 使用“最新修改时间”选主 run。  
这会把 smoke、subset、局部试验 run 误认成 canonical。

已知错误例子：

- `雪山飞狐` 被选成 `xueshanfeihu-dsv4flash-nothinking-smoke-20260511`
- 正确 canonical 应是 `xueshanfeihu-dsv4flash-v10-bgem3-clean-20260509`

**整改要求：**

必须改成以下任一方式，优先级从高到低：

1. 优先读取 `runs/jinyong/_global/canonical_runs.json`
2. 若无该文件，再按显式规则筛选 canonical run
3. 明确排除：
   - `smoke`
   - `_前五章`
   - `top5`
   - `local`
   - `comparison`
   - `query`
   - 其他明显非正式主 run 标记

**验收标准：**

- `scorecard.json` 中 15 部作品必须与 `docs/research/2026-05-12-jinyong-corpus-scorecard.md` 的 canonical 结果一致
- `total_nodes` 应回到 `30621`

### 2. `has_graph_html` 检查错误

**严重级别：中**

当前 `src/modules/jinyong/postprocess.py:101-129`：

- 字段名是 `has_graph_html`
- 实际检查的是 GraphML 缓存

这在语义上是错的。

**整改要求：**

- `has_graph_html` 必须检查 `graph.html`
- 如果需要，再额外新增 `has_graphml_cache`

### 3. 缺少跨作品污染检测

**严重级别：高**

当前 `src/modules/jinyong/postprocess.py:260-284` 仅支持：

- `generic_name`
- `english_residue`
- `bad_type`
- `low_research_value`

没有实现 spec 明确要求的 `cross_corpus_pollution`。

**整改要求：**

至少实现第一版高置信规则，例如：

1. 基于 canonical 全集先建立实体名到作品分布的索引
2. 对明显核心人物名做跨书检测
3. 如果某实体高强度属于作品 A，却出现在作品 B 且在 B 中 degree 很低、上下文支撑弱，则标成：
   - `reason_codes: ["cross_corpus_pollution"]`

**最低验收：**

- 结果里应能出现至少一批真实污染候选
- 不能继续是 `令狐冲`、`岳灵珊` 这类已知例子完全查不到

### 4. `low_research_value` 规则过粗

**严重级别：中高**

当前规则：

- `degree == 0 and (len(entity_name) <= 2 or entity_name in _GENERIC_NAMES)`

这会误伤很多合法实体，如地名、器物、典故短名。

**整改要求：**

不要单独使用“长度 <= 2”作为触发条件。  
应组合更多信号，例如：

1. `degree == 0`
2. 名称属于泛称表
3. 无描述或描述极短
4. 类型异常或缺失
5. 不属于常见高价值类型白名单

**最低要求：**

- `开封`、`皋兰` 这类显然不该直接算低价值噪声的项，不应再因为“两字 + 孤立”直接入表

### 5. 候选文件 JSON 结构不符合 spec

**严重级别：中**

当前：

- `noise_candidates.entities.json`
- `noise_candidates.relations.json`

都是 bare list。

spec 要求更适合 downstream 使用的 wrapper 结构。

**整改要求：**

至少改成：

```json
{
  "generated_at": "...",
  "corpus": "jinyong",
  "candidates": []
}
```

如果有需要，可补：

- `source`
- `candidate_type`
- `total_candidates`

### 6. 缺少测试

**严重级别：中**

当前没有针对 postprocess 的回归测试，所以主 run 选错这类问题没有被拦住。

**整改要求：**

新增最少以下测试：

1. canonical run 优先级测试
2. `has_graph_html` 字段测试
3. candidate wrapper schema 测试
4. `cross_corpus_pollution` 至少有一条候选的集成测试或 fixture 测试
5. `low_research_value` 不误伤典型合法短名的测试

## 建议新增文件

### A. canonical 清单

新增：

- `runs/jinyong/_global/canonical_runs.json`

建议结构：

```json
{
  "generated_at": "...",
  "corpus": "jinyong",
  "works": [
    {
      "novel": "雪山飞狐",
      "run_dir": "runs/jinyong/雪山飞狐/deepseek-v4-flash-zh-strict-bge-m3/lightrag/xueshanfeihu-dsv4flash-v10-bgem3-clean-20260509"
    }
  ]
}
```

### B. 归档说明

可选新增：

- `docs/research/2026-05-12-jinyong-runs-retention-policy.md`

用于解释为什么有些 run 保留但不参与默认扫描。

## 禁止事项

1. 不要修改单书原始 `graph.json`
2. 不要靠人工硬编码 15 条 metrics 到 scorecard
3. 不要继续按 mtime 猜测主 run
4. 不要为了压低噪声数量而简单减少规则输出

## 推荐实施顺序

1. 先修 canonical run 选择
2. 再修 scorecard 字段
3. 再修 candidate schema
4. 再补 `cross_corpus_pollution`
5. 再收紧 `low_research_value`
6. 最后补测试并重跑 `runs/jinyong/_global/*`

## 交付要求

完成后应提供：

1. 修改文件列表
2. 测试命令与结果
3. 新生成的：
   - `scorecard.json`
   - `scorecard.md`
   - `noise_candidates.entities.json`
   - `noise_candidates.relations.json`
   - `noise_candidates.summary.json`
4. 一段简短说明：
   - 如何确定 canonical run
   - 如何判断跨作品污染
   - 如何避免低价值规则误伤
