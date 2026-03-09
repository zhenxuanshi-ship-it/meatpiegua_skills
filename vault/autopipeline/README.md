# Autopipeline（OpenClaw + Obsidian-CLI）

这个目录是与你现有 Vault 内容隔离的自动化内容生产流水线根目录。

> 根路径约定：`vault/autopipeline/`

## 目录结构

```txt
vault/
  autopipeline/
    00_inbox/
      hot_topics/      # 热点抓取结果池
    10_research/       # 事实与素材研究
    20_ideation/       # 角度与选题拆解
    30_drafts/         # 初稿（多平台）
    40_review/         # 人工审核与合规检查
    50_published/      # 发布记录与链接回写
    60_analytics/      # 数据回流与复盘
    templates/         # 模板库
    assets/            # 封面、素材、附件
    ops/               # 批处理脚本与运行记录
```

## 内容状态机

建议用以下状态追踪每一条内容卡：

`new -> researched -> ideated -> drafted -> reviewed -> published -> analyzed`

## 建议的 OpenClaw Agent 分工

1. `trend-scout`：热点检索与去重，写入 `00_inbox/hot_topics/`
2. `researcher`：补充背景事实与证据，写入 `10_research/`
3. `angle-generator`：生成角度、标题、结构，写入 `20_ideation/`
4. `draft-writer`：按平台出稿，写入 `30_drafts/`
5. `compliance-checker`：风险检查，流转 `40_review/`
6. `publisher`：发布并回写链接到 `50_published/`
7. `analyst`：拉取指标并沉淀复盘到 `60_analytics/`

## Obsidian-CLI 最小化操作建议

- 创建新热点卡：使用 `templates/topic-card.md`
- 生成平台初稿：使用 `templates/platform-draft.md`
- 发布后复盘：使用 `templates/postmortem.md`

你可以在 `ops/` 下维护自己的 CLI 命令封装（如 shell 脚本或任务编排文件）。
