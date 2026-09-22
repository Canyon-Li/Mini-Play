---
name: mini-play-render
description: "将 mini-play 产出的 YAML DSL 剧本渲染成最终形态（Markdown / HTML 等）。当用户说『渲染小剧场』『把 DSL 转成 Markdown/HTML』或调用 /mini-play-render {format} {dsl-path} 时触发。"
---

# Mini-Play Render

把 [mini-play](../mini-play/SKILL.md) 产出的 YAML DSL 剧本渲染成最终形态。这是 mini-play 的"消费者"。

## 支持的渲染目标

| format | 输出 | 特点 |
|---|---|---|
| `markdown` | `.md` | 与原 mini-play Markdown 风格一致，可直接贴文档 |
| `html` | `.html` | 自包含单文件（内联 CSS/JS，离线可开），支持角色卡点击展开 + 旁白默认折叠 |

## 调用方式

```
/mini-play-render {format} {dsl-path}
```

例如：
```
/mini-play-render markdown plays/元数据知识库的诞生.yaml
/mini-play-render html plays/rag-rrf.yaml
```

## 工作流

1. **解析参数** — 拿到 `{format}`（markdown | html）和 `{dsl-path}`
2. **调用渲染器** — 执行（路径相对本 skill 目录，渲染器随 mini-play skill 一起安装）：
   ```
   python ../mini-play/render.py {format} "{dsl-path}"
   ```
3. **处理结果**：
   - 渲染成功 → 告诉用户输出文件路径（默认在剧本 YAML 所在目录，文件名 `{slug}.{ext}`）
   - schema 校验失败 → 把 pydantic 错误返回给用户，并建议"用 `/mini-play` 修复 DSL 后重渲"
   - 渲染失败 → 显示错误信息，常见原因是模板渲染问题，可建议打开 `../mini-play/templates/{format}.j2` 查看

## 输出位置

默认输出到**剧本 YAML 所在目录**：`{slug}.{ext}`（产物跟源文件放在一起，不写进 skill 安装目录），其中 `slug` 由 `play.title` slugify 而来（去掉特殊字符）。

如需指定输出路径：
```
python .../render.py markdown input.yaml --out path/to/output.md
```

## 何时触发

- 用户显式说 `/mini-play-render ...`
- 用户在拿到 DSL 后说"渲成 Markdown"/"渲成 HTML"/"把这个剧本变成网页"
- 不会在 `/mini-play` 产出 DSL 时自动触发——保持两个 skill 解耦，让用户对"何时渲染、渲染成什么"有完全控制

## 校验工具

如果用户只想校验 DSL 而不渲染：
```
python ../mini-play/schema.py plays/{name}.yaml
```

成功输出 `OK: {title} ({N} acts, {M} characters)`，失败输出 `INVALID: {错误详情}`。
