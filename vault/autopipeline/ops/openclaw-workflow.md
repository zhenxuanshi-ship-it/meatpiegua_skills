# OpenClaw 工作流（MVP）

## 目标
把“热点检索 -> 创意 -> 创作 -> 发布 -> 复盘”变成可重复执行的任务流。

## 调度顺序
1. `trend-scout`（每日）
2. `researcher`（每日，处理 Top N）
3. `angle-generator`（每日）
4. `draft-writer`（每日）
5. `compliance-checker`（发布前）
6. `publisher`（按排期）
7. `analyst`（D+1 / 周复盘）

## 输入输出约定
- 所有节点输入输出均使用 Markdown 文件（Frontmatter + 正文）
- 节点只更新自己负责的字段，避免互相覆盖

### 关键字段
- `status`: 状态机字段
- `from_topic`: 从哪个选题卡衍生
- `risk_level`: low / medium / high
- `next_action`: 下一步动作

## 评分建议
`total_score = 0.4*heat + 0.3*relevance + 0.2*creatability + 0.1*(100-competition)`

> 先保证“可跑通”，再逐步接入更复杂的模型评分。
