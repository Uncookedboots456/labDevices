# 三方协作记录与 AI 恢复手册

记录本项目 UML 建模采用的“架构 → 评审 → 检查”三方流程：谁用什么模型、干了什么、可复用的提示词，
以及会话中断后如何恢复。图表清单与重新生成方法见 `docs/models/README.md`。

## 1. 角色、模型与工具

| 线 | 工具 | 模型（启动参数） | 职责 | 典型产出 |
| --- | --- | --- | --- | --- |
| 总架构 `arch` | Antigravity CLI（`agy`） | `--model gemini-4-argon-high` | 领域概念划分、泳道职责交接、是否超出用例范围 | 5 条按影响排序的修改建议 + 架构结论 |
| 评审 `review` | pi | `--model xai/grok-4.7:xhigh` | UML 规范、可读性、与报告正文/AGENTS.md 追溯 | 分级问题清单（严重/中/轻）+ 交付结论 |
| 检查 `check` | codex CLI | `--model gpt-6.1-sol -c model_reasoning_effort=high` | 只做可验证事实：编号、引用完整性、文件时间戳 | 结论表 + 通过/不通过 |
| 调度与落地 | pi（本会话，`cc-switch-deep-seek/deepseek-flash`） | 当前会话模型 | 画图、改 XML、导出、按意见返工 | `docs/models/*.drawio` 与 PNG |

模型 id 需按本机实时可用性确认：`agy models`、pi 的 `models-store.json`、`codex` 的
`tui.model_availability_nux`。换模型只改启动参数，不改提示词。

当前会话位置（`herdr agent list` 可复核；工作区迁移后 ID 会变）：

| pane | 名称 | 工具 | 说明 |
| --- | --- | --- | --- |
| `wN:p1` | — | pi | 调度与落地（本会话） |
| `wN:p2` | `arch` | agy | 总架构 |
| `wN:p3` | `check` | codex | 事实核验 |
| `wN:p4` | `review` | pi（resume） | 评审；重启会话后是“Resumed session”，名称需重新 `rename` |

## 2. 实际做了什么（按轮次）

对象：图2-2 类图、图2-13/14/15 三张活动图（draw.io 重绘，替换报告中同号插图）。

| 轮次 | 参与 | 结论 |
| --- | --- | --- |
| 1 | review | 4 条中级（缺合并节点、UC9 命名误导、UC2 缺设备不可达/日志失败分支、终止节点不是牛眼）+ 4 条轻微；结论：需修改 |
| 1 | arch | 5 条（类图缺 UC5/UC10/EXT2 概念、UC2 缺 INC3/INC1 拆分与设备不可达、UC11 缺 EXT2 标注与保存失败、UC9 缺通信失败分支、权限关联与日志职责耦合）；结论：需修改 |
| 1 | check | 编号、类名、XML 引用、PNG 时间戳全部通过 |
| 2 | review | 查出 2 处真实悬空：UC2「接收拒绝结果」没有连到终止；UC9「取得状态？」没有任何入边（通信失败会绕过判断直达 EXT1）；另指出 PNG 早于 drawio |
| 2 | arch | 3 条已解决、2 条部分解决；对“不新增两个类”的决定表示接受（超出报告 4.3 节既定范围） |
| 2 | check | 不通过：三张活动图 PNG 早于 drawio（确实是我改了 drawio 没重导） |
| 3 | review | 两处悬空已修复、无新断边；结论：可交付 |
| 3 | arch | 控制流闭合可达、职责与扩展条件符合基准；结论：可交付 |

结论采纳情况：全部采纳并落实；仅“给类图加 UC10 运维动作类与 EXT2 建议类”未采纳，理由写进图内注释
（无已确认数据概念，新增类等于新增需求），arch 复评接受。

### 返工要点（复用清单）

- 每个非初始节点必须有入边，每个非终止节点必须有出边——`gen_models.py` 已内置断言，先跑脚本再导出。
- 两条以上分支汇入同一动作前要有合并节点；分叉/汇合都用菱形，别用“多入边动作”冒充。
- 活动图终止节点用 UML 牛眼（外环 + 实心），不要与初始节点同形。
- 泳道名称要能排除无权角色（“人员”改为“实验人员（含管理员）”）。
- 未确认规则写成“待明确”，不能因为图好看就编出阈值、状态集或审批流。
- 改完 `.drawio` 必须重导 PNG，否则检查线会以时间戳判不通过。

## 3. 提示词模板

通用约定（三条线都适用）：**只读不改文件**、给文件绝对或仓库相对路径、要求分级 + 明确交付结论句式、
限制行数、引用证据（文件名 + 元素 + 原文位置）。

### 3.1 总架构

```text
只做建模审查，不改文件，给结论。

项目 <仓库路径>。需求基准 AGENTS.md + docs/lab-device-usecase.drawio；
写作标准 docs/report-writing-standard.md 4.2–4.5 节。

审查对象（draw.io 源与导出图）：<逐个列出 .drawio 与 .png，并注明对应报告图号>

审查重点（架构/建模层，不看排版细节）：
1) 类职责划分是否漏掉关键概念（申请与工单关系、日志与审计分离、权限关联多重性是否支撑 UC6 与 INC1）。
2) 泳道与职责交接：外部设备是否越权执行、AI 是否被画成可操作设备、自动建单是否错误连到自动化运维。
3) 是否覆盖包含行为与扩展点条件，是否缺认证失败/设备不可达/AI 不可用/保存失败分支。
4) 是否有图外新增需求（超出 19 个用例）。

输出：最多 5 条最重要的修改建议，按影响排序，每条一句话原因 + 一句话改法；
末尾一句【架构结论：可交付/需修改】。中文，不超过 25 行。
```

### 3.2 评审

```text
评审任务：UML 图评审（不要改文件，只出问题清单）。

背景：<仓库路径>。需求基准 AGENTS.md（19 用例、5 参与者、5 include/2 extend/3 泛化）；
写作标准 docs/report-writing-standard.md 第 4.2–4.5 节。
待评审图（重绘报告同号插图，需与正文一致）：<文件列表>

评审维度：1) 与 AGENTS.md 的追溯（有无图外新增角色/用例/流程）；2) UML 正确性（类图分区与多重性、
活动图起止/合并/判断标注/泳道交接）；3) 与报告正文对应；4) 可读性（文字密度、箭头穿越、缺说明）。

输出：【严重】/【中】/【轻】分级；每条给文件名 + 具体元素 + 建议改法；
最后一句总体结论（可交付 / 需修改后交付）。中文，不超过 40 行。
```

### 3.3 检查

```text
只做事实核验，不改文件，用 1 张结论表回答。

项目 <仓库路径>。需求基准 AGENTS.md（19 个用例：UC1-11、INC1-3、EXT1-2、G1-3；5 参与者）。

核验对象 <文件列表>：
1) 图内每个 UC/INC/EXT/G 编号是否都在 AGENTS.md 定义内？列出越界编号。
2) 是否出现未定义的参与者名称？
3) 类名是否与 docs/report-build/build_report.py 的 class_diagram() 一致？
4) PNG 是否由当前 .drawio 导出（比较修改时间）？
5) XML 是否可解析、source/target/parent 引用是否都存在？

输出：一张表（检查项 | 结果 | 证据）+ 一句【通过/不通过】。不超过 25 行。
```

### 3.4 返工轮次（关键：让评审核对而不是重评）

```text
第 N 轮评审（已按你上轮意见修改）。不要改文件。

已改：<逐条列出改了什么、改在哪>
未改：<列出未采纳项 + 理由>

请核对上述修改是否解决你的意见（逐条：已解决/部分/未解决），
并对“未采纳”的决定给出接受或反对（一句话理由）。
只报仍然存在的问题（如无则明确写“无”）。最后一句【可交付】/【仍需修改】+ 理由。不超过 25 行。
```

### 3.5 其余图型（重绘时直接套用）

序列图 / 通信图（同一场景成对出现时，要求两图消息编号逐条一致）：

```text
评审任务：<场景名> 的序列图与通信图一致性（不改文件）。
依据：AGENTS.md 的 <用例 ID>；docs/report-writing-standard.md 4.4 节；报告正文该场景的
基本流程与备选流程段落（docs/实验室异构设备智能运维管理系统-UML项目报告.docx）。
检查：1) 每个消息是否有发起对象、接收对象和明确编号；2) 序列图与通信图编号是否一一对应；
3) 条件消息是否只在满足条件时出现（例如 EXT1/EXT2 的条件段）；4) 是否出现正文没有的对象
或步骤；5) 返回值消息与调用消息是否区分。
输出：【严重】/【中】/【轻】+ 文件名与消息编号 + 改法；末尾【可交付/需修改】。不超过 30 行。
```

状态图（先定对象，再定状态，最后定转换）：

```text
评审任务：状态图（不改文件）。
对象：<设备状态观测摘要 / 故障工单信息>；依据 AGENTS.md 与写作标准 4.6 节。
检查：1) 是否只描述稳定状态而不是界面操作步骤；2) 初始/终止、状态名、事件[条件]/动作是否齐全；
3) 状态集合与合法转换是否有依据，未确认的状态集是否标“待明确”；4) 是否与活动图/用例说明冲突。
输出：【严重】/【中】/【轻】+ 元素 + 改法；末尾结论。不超过 25 行。
```

构件图与部署图（分开评审，不要合称“部署模型”）：

```text
评审任务：构件图与部署图（不改文件）。
依据：写作标准 4.7 节；本机方案未定（软路由或局域网 Linux 主机），只允许候选部署。
检查：1) 构件是否按职责划分而非“一类一构件”；2) 依赖方向与用例追溯是否成立；3) 部署节点、
通道、协议是否标为待定而不是凭空确定；4) AI 服务与异构设备是否放在边界外正确位置。
输出：分级问题 + 结论。不超过 25 行。
```

## 4. 恢复方法

### 4.1 先看当前状态

```bash
herdr agent list                       # 名称、pane id、状态
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
herdr pane layout --pane "$HERDR_PANE_ID"
```

名称（`arch`/`review`/`check`）会随工作区/会话变化被清空，那时直接用 pane id。ID 会变（例如
`w5:p2` → `wN:p2`），不要照抄旧 ID。

### 4.2 重新拉起三条线

```bash
# 布局：当前 pane 右上 / 左下 / 右下（宽 pane 向右切，窄或高的 pane 向下切）
herdr pane split --current --direction right --ratio 0.5 --cwd "$PWD" --no-focus
herdr pane split <p1> --direction down --ratio 0.5 --cwd "$PWD" --no-focus
herdr pane split <p2> --direction down --ratio 0.5 --cwd "$PWD" --no-focus

herdr agent start arch   --kind agy   --pane <p2> --timeout 60000 -- --model gemini-4-argon-high
herdr agent start review --kind pi    --pane <p4> --timeout 60000 -- --model xai/grok-4.7:xhigh
herdr agent start check  --kind codex --pane <p3> --timeout 90000 \
  -- --model gpt-6.1-sol -c model_reasoning_effort=high
```

### 4.3 发任务与取结果

```bash
herdr agent prompt review "<提示词>" --wait --timeout 420000
herdr agent wait review --timeout 400000
herdr agent read review --source recent-unwrapped --lines 200
herdr agent get  review                    # 状态与 pane
```

### 4.4 已知坑

- `agent_prompt_stalled`：5 秒内没观察到 working（长思考的首包延迟），提示通常已送达；改用
  `agent wait` + `read` 取结果，别重复提交。
- `agent_not_ready`（agy 首次启动）：停在“是否信任此文件夹”弹窗，确认后 `herdr agent send-keys <name> enter`。
- 长回答可能滚出屏幕：让对方把结论写进 `docs/<名字>.md` 再读（本轮用过 `docs/_rev3.txt`，读后已删）。
- codex 有周额度，重活优先给 arch/review；`check` 只派可机械核对的项。
- Windows 上 `drawio` 首次调用是拉起 Electron，几秒起步；批量导出用 `--timeout`。
- 生成器改动后先跑 `python docs/report-build/gen_models.py`（内含悬空节点断言），再逐张导出 PNG。

## 5. 图表清单（19 张，全部 draw.io 源）

模型图源及四张报告构建所需的 PNG 见 `docs/models/README.md`。其余模型按需导出预览。

| 图号 | 内容 | 源文件 |
| --- | --- | --- |
| 2-1 | 系统总体用例图 | `docs/lab-device-usecase.drawio`（图内标题仍为旧名，差异见 AGENTS.md） |
| 2-2 | 领域类图 | `class-diagram.drawio` |
| 2-3 / 2-4 | UC2 操作设备 序列 / 通信 | `seq-uc2-operate` / `comm-uc2-operate` |
| 2-5 / 2-6 | UC5 接入设备 序列 / 通信 | `seq-uc5-connect` / `comm-uc5-connect` |
| 2-7 / 2-8 | UC4 人工故障报修 序列 / 通信 | `seq-uc4-report` / `comm-uc4-report` |
| 2-9 / 2-10 | UC9 监测 + EXT1 序列 / 通信 | `seq-uc9-monitor` / `comm-uc9-monitor` |
| 2-11 / 2-12 | UC11 + EXT2 序列 / 通信 | `seq-uc11-ticket-ai` / `comm-uc11-ticket-ai` |
| 2-13 | UC2 操作设备 活动图 | `activity-uc2-operate.drawio` |
| 2-14 | UC9 监测 活动图 | `activity-uc9-monitor.drawio` |
| 2-15 | UC11 处理工单 活动图 | `activity-uc11-ticket-ai.drawio` |
| 2-16 / 2-17 | 设备状态 / 工单状态 | `state-device` / `state-ticket` |
| 2-18 / 2-19 | 构件图 / 部署图 | `component` / `deploy` |

评审记录：图 2-2、2-13～2-15 经三轮（可交付）；图 2-3～2-12 两轮（评审与检查均通过，opt 框范围与
回复虚线为返工点）；图 2-16～2-19 两轮（状态转换补「事件 [条件]」、构件补 UC6/UC7 依赖、部署外联
改从应用构件出线后判定可交付）。

图 2-2、2-13、2-14、2-15 的 draw.io 导出图已嵌入 Word 报告。

## 6. 复现图

报告依赖的四张 PNG 的导出命令见 `docs/models/README.md`。需要评审其他模型时，按需导出对应的 draw.io 图源。

## 7. 决策记录

| 日期 | 决策 | 依据 | 提出方 |
| --- | --- | --- | --- |
| 2026-11-03 | 采用“架构 → 评审 → 检查”三方流程，模型分别为 Gemini 4 Argon high / grok-4.7 xhigh / gpt-6.1-sol high | 用户指定 | 用户 |
| 2026-11-03 | 类图保持 6 个分析类，不为 UC10 运维动作与 EXT2 诊断建议建类 | AGENTS.md 范围控制 + 报告 4.3 节既定范围；已确认数据概念缺失 | 调度方，arch 复评接受 |
| 2026-11-03 | 活动图统一 3 泳道、分支汇合加合并节点、终止用牛眼 | review 第 1 轮 UML 正确性意见 | review |
| 2026-11-03 | UC9 增加“取得状态？”并把通信失败排除在异常判断之外 | arch + review 指出未知状态会绕过判断直达 EXT1 | arch/review |
| 2026-11-03 | 图源与生成器入仓（`docs/models/`、`docs/report-build/gen_models.py`），生成器内置悬空节点断言 | 手改 XML 两次漏连线，需自动拦截 | 调度方 |
| 2026-11-03 | 暂不把新图嵌入 docx | 缺 `python-docx`，且需改 `build_report.py` 引用 | 调度方 |
| 2026-11-03 | 场景消息清单抽到 `docs/report-build/scenes.py`，序列图/通信图与正文共用 | 10 张交互图与正文同源，避免两处漂移 | 调度方 |
| 2026-11-03 | 全部 19 张图改为 draw.io 源，PNG 只作导出产物 | 用户要求“所有图都要用 draw.io 完成” | 用户 |

## 8. 未完成与下一步

1. **用例图标题与实际项目名不一致**：`lab-device-usecase.drawio` 内系统边界仍写“实验室设备统一管理
   与智能运维系统”，正式名称以 AGENTS.md 为准；改图时同步更新该文件，不要再造第二份基准。
2. **git**：`AGENTS.md` 与 `docs/` 仍未提交，提交前确认范围。
