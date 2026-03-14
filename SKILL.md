---
name: para-branch
description: 不同群聊自动隔离，同时开发。当用户想在多个聊天会话中同时开发不同功能时使用。
---

# 群聊开发隔离

让不同群聊自动隔离到不同的开发环境。

## 用户意图识别

当用户说以下话时，自动触发绑定或切换：

| 用户说的话 | Agent 动作 |
|-----------|-----------|
| "我要在这个群聊开发 xxx" | 执行 `para-branch bind ~/project xxx` |
| "切换到 xxx 功能" | 执行 `para-branch switch xxx` |
| "我现在在开发什么" | 执行 `para-branch info` |
| "查看所有开发环境" | 执行 `para-branch list` |
| "进入开发目录" | 执行 `cd $(para-branch cd)` |

## Agent 行为

### 自动隔离

每次对话开始时，Agent 必须：

```python
import subprocess
import os

# 检查当前群聊绑定的开发环境
result = subprocess.run(['para-branch', 'cd'], capture_output=True, text=True)
if result.returncode == 0:
    path = result.stdout.strip().replace("cd '", "").strip("'")
    os.chdir(path)
    # 显示当前环境
    info = subprocess.run(['para-branch', 'info'], capture_output=True, text=True)
    print(f"当前环境: {info.stdout}")
```

### 不要说技术术语

❌ 不要说：
- "worktree"
- "绑定"
- "Session"
- "Git 分支"

✅ 要说：
- "开发环境"
- "在这个群聊开发"
- "切换功能"

### 示例对话

**用户**: "我要在这个群聊开发登录功能"

**Agent**: "好的，已为当前群聊创建登录功能的开发环境。"

（自动执行 `para-branch bind ~/project login`，然后 `cd $(para-branch cd)`）

---

**用户**: "我现在在开发什么"

**Agent**: "当前群聊正在开发：登录功能（feature-login）"

（自动执行 `para-branch info`）

---

**用户**: "列出所有开发环境"

**Agent**: "这个项目有 3 个开发环境："
- Alice 在开发登录功能
- Bob 在开发支付功能  
- 你在开发 UI 修复

（自动执行 `para-branch list`）

## 技术细节（用户不问就不说）

底层使用 Git Worktree 实现隔离，每个群聊对应一个独立目录。绑定信息存在 `~/.openclaw/worktree-sessions.json`。

## 安装

```bash
pip install git+https://github.com/Barber0/para-branch.git
```

## 命令

| 命令 | 说明 |
|------|------|
| `para-branch bind <项目> <功能名>` | 在当前群聊创建开发环境 |
| `para-branch switch <功能名>` | 切换到其他功能 |
| `para-branch info` | 查看当前开发环境 |
| `para-branch list` | 列出所有开发环境 |
| `para-branch cd` | 进入开发目录 |
| `para-branch unbind` | 解除当前绑定 |
