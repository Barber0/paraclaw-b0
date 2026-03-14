---
name: paraclaw-b0
description: Git Worktree Session Manager - Bind chat sessions to independent Git worktrees for parallel branch development. When you need to work on multiple Git branches simultaneously across different chat sessions, with each session isolated in its own worktree.
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["python3", "git"] },
        "install":
          [
            {
              "id": "pip",
              "kind": "pip",
              "package": "-e /root/.openclaw/workspace/paraclaw-b0",
              "bins": ["paraclaw"],
              "label": "Install paraclaw-b0 via pip"
            }
          ]
      }
  }
---

# paraclaw-b0

让不同的聊天会话各自工作在独立的 Git Worktree 中。

## 核心概念

不同群聊同时操作同一个代码仓库，各自在不同的分支上，互不干扰。

## 快速开始

```bash
# 安装
pip install git+https://github.com/Barber0/paraclaw-b0.git

# 绑定当前群聊到分支
paraclaw bind ~/myproject feature-xxx

# 查看当前绑定
paraclaw info

# 进入工作目录
cd $(paraclaw cd)

# 切换到新分支
paraclaw switch feature-yyy

# 查看所有绑定
paraclaw list
```

## 自然语言使用

可以直接说：
- "在这个群聊绑定 feature-xxx 分支"
- "查看当前绑定的分支"
- "切换到 bugfix 分支"
- "列出所有人的绑定"

## 与 OpenClaw 集成

### Agent 必须自动检测 Worktree

```python
import subprocess
import os

# 获取当前 worktree
result = subprocess.run(['paraclaw', 'cd'], capture_output=True, text=True)
if result.returncode == 0:
    worktree = result.stdout.strip().replace("cd '", "").strip("'")
    os.chdir(worktree)
    print(f"已进入 worktree: {worktree}")

# 获取当前分支
info = subprocess.run(['paraclaw', 'info'], capture_output=True, text=True)
print(info.stdout)
```

### Agent 行为规则

| 用户场景 | Agent 行为 |
|---------|-----------|
| "我们在做哪个分支" | 运行 `paraclaw info` |
| "查看代码" | 先 `cd $(paraclaw cd)` |
| "修改 xxx 文件" | 确保在 worktree 目录操作 |
| "绑定到 xxx 分支" | 执行 `paraclaw bind` |

**禁止行为：**
- ❌ 不检查绑定直接操作主目录
- ❌ 假设用户在主分支工作

**正确行为：**
- ✅ 每次对话开始先 `paraclaw info`
- ✅ 自动切换到绑定的目录
- ✅ 显示当前分支和路径

## 多用户支持

同一台机器上多个用户自动隔离：
- 不同用户名 → 不同 worktree 路径
- `paraclaw list` 显示所有人的绑定

## 存储位置

- 绑定信息：`~/.openclaw/worktree-sessions.json`
- Worktrees：`{repo}-worktrees/{user}_{branch}/`

## 许可证

MIT - [Zilin Fang](https://github.com/Barber0)
