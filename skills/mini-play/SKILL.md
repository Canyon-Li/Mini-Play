---
name: mini-play
description: "将复杂的技术概念、架构、流程转化为多人小剧场对话。本 skill 产出一份结构化的 YAML DSL（剧本源文件），由独立的 mini-play-render skill 渲染成 Markdown / HTML 等最终形态。当用户要求『用小剧场解释』『做成对话形式』或提及『剧场』『对话』『角色扮演』等关键词时触发。也可用 /mini-play {主题} 直接调用。"
---

# Mini-Play

把复杂的技术概念、系统架构或工作流程转化成一个**结构化的 YAML 剧本（DSL）**——剧本里每个角色、每句台词、每个旁白都是一等公民。Markdown / HTML 等最终形态由 [mini-play-render](../mini-play-render/SKILL.md) skill 调用渲染器生成。

> **不要直接写 Markdown。** 你的产物是 `.yaml` 文件，不是 `.md` 文件。Markdown 只是 DSL 的渲染结果之一。

## 风格原则（软约束）

这些是创作时的指南，靠 prompt 自觉遵守：

1. **场景化开场** — 用 `scene` 字段交代背景
2. **角色驱动** — 每个角色有自己的 `persona` 和 `backstory`，用对话推进而不是直接陈述
3. **矛盾推进** — 通过角色之间的问答、矛盾、协作推动叙事（"问题出现 → 逐步解决 → 最终分工"三段式）
4. **白话为主** — 避免术语堆砌，用比喻和日常语言解释技术概念
5. **情感化** — `line` beat 可标 `emotion`（困惑 / 惊讶 / 得意 / 无奈 / 兴奋 / 平静 / 焦虑 / 思考）
6. **分幕结构** — 用 `acts` 分节，每幕解决一个子问题
7. **谢幕总结** — `closing.table` 列各角色职责，`closing.thesis` 一句话点题

## DSL Schema

完整字段如下（**加粗**为必填）：

```yaml
**title**: 一句话标题
**scene**: 全局场景说明（开场背景）
**characters**:            # 至少 1 个
  - **name**: LLM
    **persona**: 一句话人设
    aliases: [大模型, AI]              # 别名/外号
    backstory: 详细背景                # 角色卡点击展开看（HTML 渲染专用）
    appearance: 外观描述               # 互动话剧备用
**acts**:                  # 至少 1 个
  - **title**: 第一幕：xxx
    scene: 该幕专属场景（可选，覆盖全局）
    **beats**:             # 至少 1 个，每条 beat 必填 type 字段
      # 6 种 beat 类型：
      - **type**: line                  # 台词
        **who**: LLM
        emotion: 困惑                   # 困惑|惊讶|得意|无奈|兴奋|平静|焦虑|思考
        **text**: |
          多行台词……
      - **type**: thought               # 内心独白（"心里想"）
        **who**: LLM
        **text**: ……
      - **type**: stage_direction       # 舞台说明 / 叙事归纳
        **text**: LLM 面露困惑
        label: 问题                     # 可选，渲染为 "**问题：** xxx"
      - **type**: aside                 # 旁白（"为什么需要这步"）
        variant: note                   # note | warning | insight（默认 note）
        **text**: ……
      - **type**: code                  # 代码块
        **lang**: sql                   # 必填
        title: 可选标题
        **text**: |
          SELECT ...
      - **type**: transition            # 转场（幕间分隔）
        **text**: 时间过去了三天
**closing**:
  table:                               # 可选
    **headers**: [角色, 做什么]
    rows: [[LLM, xxx], ...]
  **thesis**: 核心思想一句话（黑体收尾）
render_meta:                            # 可选，渲染器专属配置
  html:
    aside_collapse_default: true        # 旁白默认折叠（HTML 渲染用）
    theme: light                        # light | dark
```

## 校验与 lint 规则

**硬约束**（pydantic schema 强制校验，不通过则 render 失败）：
- `beat.who` 必须在 `characters[].name` ∪ `aliases` 中（引用完整性）
- `code` beat 必须有 `lang`
- `emotion` / `aside.variant` 必须是枚举值
- `acts` / `characters` 至少 1 项；每 act 的 `beats` 至少 1 项
- 不允许多余字段（防 typo）

**软 lint**（产出后请你在思考里自检）：
- 每个角色至少发言 1 次（不要让某角色"裸登场"然后消失）
- 不允许"独白幕"——一幕里同一角色连续 4 条以上独白（拆成对话或加 stage_direction）
- 谢幕表 `rows` 应覆盖所有登场角色
- `thesis` 不要超过 100 字

## 创作工作流

收到 `/mini-play {主题}` 后按以下步骤：

1. **先在思考里列角色档案**——哪些组件/人物/系统要登场，每个角色的 `persona` 是什么
2. **草拟分幕大纲**——按"问题出现 → 逐步解决 → 最终分工"三段式切 N 幕
3. **输出完整 YAML**——按 schema 填充所有字段，台词用 YAML 块标量（`|` 或 `>-`）保留多行
4. **自检 lint 软规则**——扫一遍：有没有角色裸登场？有没有独白幕？thesis 长度？
5. **保存到** 用户当前工作目录下的 `plays/{slug}.yaml`（没有则创建。剧本属于用户项目，不要写进 skill 安装目录——那里只放本 skill 自带的示例剧本）
6. **告诉用户文件路径**，并提示：调用 `/mini-play-render markdown {path}` 或 `/mini-play-render html {path}` 来生成最终产物

## 文件命名

- 文件名用中文或英文均可，但避免特殊字符 `\ / : * ? " < > |`
- 文件名建议：`{主题简称}.yaml`，如 `rag-rrf.yaml` 或 `元数据知识库的诞生.yaml`

## 调用方式

- 提示中包含"用小剧场解释"、"做成对话"、"输出到小剧场"、"/mini-play" → 自动触发
- 直接在对话中说 `/mini-play {你想解释的主题}`

## 参考示例

两个完整的 DSL 示例（由原 Markdown 示例反向迁移而来）：

- [plays/元数据知识库的诞生.yaml](plays/元数据知识库的诞生.yaml) — 构建阶段（5 角色：LLM、元数据库、Qdrant、ES、元数据知识库）
- [plays/LLM的12步喂饭之旅.yaml](plays/LLM的12步喂饭之旅.yaml) — 查询阶段（2 角色：LLM、Graph，9 幕）

这两个示例覆盖了 schema 的所有 beat 类型，是创作新剧本时的最佳参考。
