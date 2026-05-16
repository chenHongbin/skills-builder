# 书籍镜子 (Book Mirror)

> 把任何文字变成一面镜子——左边是作者，右边是你自己。

受 [Garry Tan](https://x.com/garrytan/status/2049059060427952164) 启发。普通的 AI 书摘人人适用，也就人人没用。书籍镜子不同：它读取 AI 对你的全部了解——你的项目、挑战、决策、价值观——然后告诉你**这些文字对你具体意味着什么**。

不只是书——公众号文章、朋友圈、推文、报告，任何你想深度理解的文字都可以。

---

## 它跟普通 AI 摘要有什么不同？

| 普通 AI 摘要 | 书籍镜子 |
|:-----------|:-------|
| "这本书讲了 3 个核心观点..." | "你在决定是推功能 A 还是 B，作者的建议是..." |
| 对所有人都一样 | 每一份分析都是给你的 |
| 读完不知道跟我有什么关系 | 右栏直接告诉你：这对你意味着什么 |
| 左栏=内容总结，右栏=另一份总结 | 左栏=作者的观点，右栏=**你**的行动指南 |

**特异性测试：** 把右栏内容里的"你"替换成"[某人]"，如果读起来仍然像有效建议——那就太泛了。好的右栏去个性化后会变得毫无意义。

---

## 能处理什么内容？

| 输入类型 | 支持 | 说明 |
|---------|:--:|------|
| PDF 书籍 | ✅ | 自动提取章节，逐章两栏分析 |
| EPUB 书籍 | ✅ | 内置脚本，零依赖 |
| 微信公众号文章 | ✅ | 内置提取（零依赖），贴链接就行 |
| X/Twitter 推文 | ✅ | 建议装 x-fetcher skill |
| 小红书 | ✅ | 建议装 x-reader skill |
| 直接粘贴文字 | ✅ | 自动判断长短，走对应模式 |
| 朋友圈/社交媒体 | ✅ | 短内容一次性分析 |
| 网页链接 | ✅ | 自动抓取 |
| 英文书籍 | ✅ | 关键引用保留原文+翻译 |

---

## 安装方法（一步一步跟着做）

```bash
# 1. 创建 skill 目录
mkdir -p ~/.claude/skills/book-mirror/scripts

# 2. 下载文件（二选一）
# 方式 A：克隆整个仓库
git clone https://github.com/chenHongbin/skills-builder.git /tmp/skills-builder
cp /tmp/skills-builder/skills/book-mirror/skill.md ~/.claude/skills/book-mirror/
cp /tmp/skills-builder/skills/book-mirror/scripts/*.py ~/.claude/skills/book-mirror/scripts/

# 方式 B：直接下载单个文件（从 GitHub 页面）
# 下载 skill.md → ~/.claude/skills/book-mirror/skill.md
# 下载 scripts/extract_epub.py → ~/.claude/skills/book-mirror/scripts/extract_epub.py
# 下载 scripts/detect_chapters.py → ~/.claude/skills/book-mirror/scripts/detect_chapters.py
```

**不需要安装任何 Python 依赖**——提取脚本只用了 Python 标准库（`zipfile`、`xml`、`re`、`html.parser`），开箱即用。

**可选：** 如果要分析 PDF 文件，需要装 Poppler：
```bash
brew install poppler
```

---

## 怎么用？

在 Claude Code 里说：

```
分析这本书
/Users/robertchen/Downloads/段永平投资问答录.pdf
```

或者贴一篇公众号文章：

```
帮我解读这篇文章
https://mp.weixin.qq.com/s/pcPVcjeZrKMGQ-YMjaaBMA
```

或者直接粘贴一段文字：

```
分析这段文字
[粘贴任何文字]
```

触发词：`分析这本书`、`书镜`、`book mirror`、`帮我读`、`逐章解读`、`这本书对我有什么用`、`分析这篇文章`、`帮我解读这段`

---

## 实际效果

**输入：** 一条朋友圈——"最好的销售不是说服客户，而是让客户自己说服自己。"

**输出：**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 朋友圈 (约 50 字)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

核心主旨：销售的关键不是口才，而是提问——让客户在问题中自己发现需求。

| 作者说了什么 | 这对你意味着什么 |
|:------------|:----------------|
| 销售的本质是"让客户自己说服自己"，而非销售去说服客户。 | 你的团队在推 AI 套电机器人时，最大的对手不是竞品，而是医院客户觉得"人工客服也还行"。与其告诉他们 AI 更好，不如问："上个月你们漏接了多少钱的咨询？" |
| "问出那个让他停下来想的问题"——高质量的问题比高质量的话术更有转化力。 | 你的 SOP 话术库里有应答模板，但有没有"必问问题库"？让每个销售整理 3 个客户一听就停下来的问题。 |

💡 这段内容对你最关键的一句话：比起打磨完美话术，更重要的是设计让客户自己发现问题的问题。
```

---

## 配套技能（可选安装）

这些 skill 能帮 book-mirror 更好地读取特定平台的内容：

| 技能 | 用途 | 链接 |
|------|------|------|
| x-fetcher | 读取 X/Twitter 推文 | https://github.com/Jane-xiaoer/x-fetcher |
| x-reader | 读取小红书内容 | https://github.com/runesleo/x-reader |

> 注：微信公众号已内置支持，**不需要**装任何配套技能。

---

## 设计理念

- **左栏忠实呈现作者**——不是 AI 的概括，是作者的实际论点
- **右栏精准映射你**——读起来像一个了解你的人在书页空白处给你写批注
- **如果与你无关，直说**——不强行关联，短的坦白比长的编造强
- **每一条都指向你的具体情境**——不生成泛泛而谈的建议

6 个常见反模式（我们刻意避免的）：书评式复述、星座运势式模糊表达、啦啦队式奉承、第二堂课式讲解、幽灵式空洞点评、编故事式猜测。

---

## 作者

由 Claude Code + 人类协作构建。

**来源：** [Garry Tan 的 Book Mirror 概念](https://x.com/garrytan/status/2049059060427952164)

**许可证：** MIT
