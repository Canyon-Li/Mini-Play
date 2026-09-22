# MiniPlay 🎭

> 把复杂的技术概念、架构、流程，变成一场人人看得懂的小剧场。

![screenshot](docs/screenshot.png)

## 这是什么

MiniPlay 是一组 [Claude Code](https://code.claude.com) skill，用**角色扮演对话**来解释技术概念。它由两个解耦的 skill 组成：

| Skill | 职责 |
|---|---|
| `mini-play` | **创作** —— 把主题写成结构化 YAML 剧本（DSL），角色、台词、旁白、代码块、谢幕总结都是一等公民 |
| `mini-play-render` | **渲染** —— 把 DSL 渲染成 Markdown 或自包含 HTML |

创作与渲染解耦：一份剧本随时可以渲染成任意格式；schema 校验失败也只影响渲染，不会破坏剧本本身。

## 安装

依赖：Python ≥ 3.10，以及 `pydantic` / `jinja2` / `pyyaml`：

```bash
pip install -r requirements.txt
```

### 方式一：Plugin（推荐）

在 Claude Code 中执行：

```
/plugin marketplace add Canyon-Li/Mini-Play
/plugin install mini-play@Mini-Play
```

### 方式二：手动安装

把 `skills/` 下的两个目录复制到 `~/.claude/skills/`：

```bash
git clone https://github.com/Canyon-Li/Mini-Play.git
cp -r Mini-Play/skills/mini-play Mini-Play/skills/mini-play-render ~/.claude/skills/
```

> 两个 skill 需要一起安装：`mini-play-render` 会调用 `mini-play` 目录里的渲染器。

## 快速开始

```
/mini-play RAG 检索中的重排序
```

Claude 会产出一个 YAML 剧本（角色档案、分幕、台词、旁白、谢幕表），然后按需渲染：

```
/mini-play-render html <剧本路径>       # 自包含 HTML，离线可开
/mini-play-render markdown <剧本路径>
```

## DSL 一瞥

```yaml
title: 元数据知识库的诞生
scene: 一个 AI 项目小组在讨论"怎么让 LLM 知道数据库里有什么"
characters:
  - name: LLM
    persona: 会写 SQL 但不知道数据库里有什么的 AI
    aliases: [大模型]
    backstory: 上下文窗口有限，吃不下整库的原始元数据。
acts:
  - title: 第一幕：没有知识库的时候
    beats:
      - type: line
        who: LLM
        emotion: 困惑
        text: 我可以写 SQL，但……你数据库里有什么表？
      - type: aside
        variant: insight
        text: 为什么需要这步 —— ……
closing:
  table:
    headers: [角色, 做什么]
    rows: [[LLM, 写 SQL]]
  thesis: 一句话点题
```

共 6 种 beat：`line`（台词）/ `thought`（内心独白）/ `stage_direction`（舞台说明）/ `aside`（旁白）/ `code`（代码块）/ `transition`（转场）。完整 schema 见 [skills/mini-play/SKILL.md](skills/mini-play/SKILL.md)，由 [schema.py](skills/mini-play/schema.py) 的 pydantic 模型强制校验（角色引用完整性、beat 必填字段、防 typo 等）。

## 示例剧本

| 剧本 | 规模 | 内容 |
|---|---|---|
| [元数据知识库的诞生](skills/mini-play/plays/元数据知识库的诞生.yaml) | 8 角色 | 构建阶段：三套索引如何分工 |
| [LLM的12步喂饭之旅](skills/mini-play/plays/LLM的12步喂饭之旅.yaml) | 2 角色 / 9 幕 | 查询阶段：一次 Text2SQL 的完整旅程 |

渲染出的 HTML 是**自包含单文件**（内联 CSS/JS，离线可开），支持：

- 点击角色名弹出**角色卡**（人设 / 别名 / 背景 / 登场幕次）
- 旁白（note / warning / insight）默认折叠，不打断剧情
- 幕间导航、深色主题（`render_meta.html.theme: dark`）

## 渲染器 CLI（不依赖 Claude 也可用）

```bash
python skills/mini-play/schema.py <剧本.yaml>            # 只校验
python skills/mini-play/render.py html <剧本.yaml>       # 渲染 HTML
python skills/mini-play/render.py markdown <剧本.yaml>   # 渲染 Markdown
python skills/mini-play/render.py html <剧本.yaml> --out out/x.html
```

## License

[MIT](LICENSE)
