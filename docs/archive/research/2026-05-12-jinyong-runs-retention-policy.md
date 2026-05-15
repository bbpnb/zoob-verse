# 金庸 `runs/` 保留与归档约定

本文档的目标不是讨论模型优劣，而是解决一个更实际的问题：

- `runs/jinyong/` 里既有主结果，也有 smoke、subset、comparison、cross、局部 query 实验
- 人或 AI 直接扫描目录时，很容易把“最新的 run”误当成“主 run”
- 这会直接污染后处理、scorecard、噪声清单和后续研究

因此需要一份明确的保留与归档约定。

## 一句话原则

`runs/` 保留主结果与关键实验，但必须让“主结果”和“非主结果”在目录层面可区分。

不是所有实验都要删。  
但不应让实验 run 和主 run 混在一起，靠修改时间猜。

## 目录角色

当前 `runs/jinyong/` 下的内容，按角色分为四类：

1. **主结果**
   - 每部作品一个代表性 run
   - 供 scorecard、后处理、跨作品研究默认使用

2. **对比实验**
   - 不同模型、预算、provider、prompt 的比较
   - 价值主要在经验记录，不应参与主结果扫描

3. **子集/烟雾测试**
   - 例如前五章、smoke、local quick run
   - 只用于验证流程或做局部判断，不应参与主结果扫描

4. **跨作品研究产物**
   - `cross/`
   - 是派生研究结果，不是单书基础图谱

## 当前主结果 canonical 清单

后续任何自动扫描、scorecard、后处理，都应默认以这 15 个 run 为准，而不是按最新修改时间猜测。

| 作品 | canonical run_dir |
| --- | --- |
| 白马啸西风 | `runs/jinyong/白马啸西风/deepseek-v4-flash-zh-strict-bge-m3/lightrag/baimaxiaoxifeng-dsv4flash-v10-bgem3-20260509` |
| 鸳鸯刀 | `runs/jinyong/鸳鸯刀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuanyangdao-dsv4flash-v10-bgem3-20260508` |
| 越女剑 | `runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507` |
| 连城诀 | `runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-clean-20260509` |
| 雪山飞狐 | `runs/jinyong/雪山飞狐/deepseek-v4-flash-zh-strict-bge-m3/lightrag/xueshanfeihu-dsv4flash-v10-bgem3-clean-20260509` |
| 飞狐外传 | `runs/jinyong/飞狐外传/deepseek-v4-flash-zh-strict-bge-m3/lightrag/feihuwaizhuan-dsv4flash-v10-bgem3-clean-20260509` |
| 书剑恩仇录 | `runs/jinyong/书剑恩仇录/deepseek-v4-flash-zh-strict-bge-m3/lightrag/shujianenchoulu-dsv4flash-v10-bgem3-clean-20260510` |
| 碧血剑 | `runs/jinyong/碧血剑/doubao-seed-1.6-openrouter-bge-m3/lightrag/bixuejian-doubao16-openrouter-bgem3-clean-20260510` |
| 笑傲江湖 | `runs/jinyong/笑傲江湖/deepseek-v4-flash-zh-strict-bge-m3/lightrag/xiaoaojianghu-dsv4flash-zh-strict-bgem3-20260510` |
| 侠客行 | `runs/jinyong/侠客行/doubao-seed-1.6-openrouter-bge-m3/lightrag/xiakexing-doubao16-openrouter-bgem3-clean-20260510` |
| 射雕英雄传 | `runs/jinyong/射雕英雄传/deepseek-v4-flash-zh-strict-bge-m3/lightrag/shediaoyingxiongzhuan-dsv4flash-zh-strict-bgem3-20260511` |
| 神雕侠侣 | `runs/jinyong/神雕侠侣/doubao-seed-1.6-openrouter-bge-m3/lightrag/shendiaoxialv-doubao16-openrouter-bgem3-20260511` |
| 天龙八部 | `runs/jinyong/天龙八部/deepseek-v4-flash-zh-strict-bge-m3-nothinking/lightrag/tianlongbabu-dsv4flash-nothinking-bgem3-20260512` |
| 倚天屠龙记 | `runs/jinyong/倚天屠龙记/doubao-seed-1.6-bge-m3/lightrag/yitiantulongji-doubao16-bgem3-20260512` |
| 鹿鼎记 | `runs/jinyong/鹿鼎记/deepseek-v4-flash-zh-strict-bge-m3-nothinking/lightrag/ludingji-dsv4flash-nothinking-bgem3-20260512` |

## 哪些应该保留

以下内容建议保留：

1. 15 部作品的 canonical 主 run
2. `comparisons/` 下已经形成文档结论的关键模型对比
3. `cross/` 下已经形成研究记录的跨作品结果
4. 少量高价值非主线基准 run
   - 例如 `越女剑` 的若干模型对比样本

## 哪些应该归档出主视野

以下内容不建议继续留在“会被自动扫到主结果”的位置：

1. smoke run
   - 例：`雪山飞狐/.../xueshanfeihu-dsv4flash-nothinking-smoke-20260511`

2. subset run
   - 例：`连城诀_前五章/.../lianchengjue-top5-doubao16-20260510`

3. 只用于 query 或预算试验的特殊 run
   - 例：`越女剑/gpt-5.1-bge-m3/lightrag/yuenvjian-gpt51-index-doubao16-query-*`

4. 已写进比较文档、但不再作为后续默认输入的局部试验 run
   - 例如 `越女剑` 的 `doubao-1.5-pro-32k`、`doubao-2.0-lite`、`deepseek-v3.2-pro-siliconflow`

## 建议的目录收口方式

不建议直接删除，优先采用“归档但不参与默认扫描”：

- `runs/jinyong/_archive/`
  - `smoke/`
  - `subset/`
  - `local-experiments/`
  - `query-experiments/`

这样做的好处：

- 经验资产还在
- 自动扫描不会误判
- 后续如果要回看某次试验，路径仍然可追

## 机器可读建议

只靠目录命名和人工记忆不够。  
后续应增加至少一种机器可读约定：

1. `runs/jinyong/_global/canonical_runs.json`
2. 或者每个主 run 下放一个 `run_role=canonical`
3. 或者在后处理扫描中显式读取 allowlist

当前最稳妥的是方案 1。

## 当前执行建议

当前阶段建议：

1. 保留 `comparisons/` 和 `cross/`
2. 把 smoke / subset / query-only / 局部 local run 归档到 `_archive/`
3. 增加 `canonical_runs.json`
4. 修改后处理扫描逻辑，优先读 canonical 清单，不再按 mtime 选主 run

如果后续某个旧实验完全失去参考价值，再考虑真正删除。
