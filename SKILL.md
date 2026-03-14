---
name: para-branch
description: 不同群聊绑定到不同 Git 分支，同时开发互不干扰。
---

# 群聊分支隔离

让不同群聊自动绑定到不同的 Git 分支。

## 核心概念

- 群聊 A → feature-login 分支
- 群聊 B → feature-payment 分支
- 各自独立，同时开发

## 用户意图识别

| 用户说的话 | Agent 动作 |
|-----------|-----------|
| "我要在这个群聊开发 feature-xxx" | `para-branch bind ~/project feature-xxx` |
| "切换到 feature-yyy 分支" | `para-branch switch feature-yyy` |
| "当前在哪个分支" | `para-branch info` 或 `git branch` |
| "我在编辑哪个目录" | `para-branch info` 显示 worktree 路径 |
| "列出所有分支" | `para-branch list` |
| "进入开发目录" | `cd $(para-branch cd)` |

## 处理分支查询

当用户问分支或目录时，必须准确回答：

```python
import subprocess

# 获取当前分支和目录
info = subprocess.run(['para-branch', 'info'], capture_output=True, text=True)
if info.returncode == 0:
    print(info.stdout)  # 显示分支名和目录路径

# 或直接用 git
git_branch = subprocess.run(['git', 'branch', '--show-current'], 
                           capture_output=True, text=True).stdout.strip()
pwd = subprocess.run(['pwd'], capture_output=True, text=True).stdout.strip()

print(f"当前分支: {git_branch}")
print(f"当前目录: {pwd}")
```

## Agent 自动行为

每次对话开始：

```python
import subprocess
import os

# 检查当前绑定
result = subprocess.run(['para-branch', 'cd'], capture_output=True, text=True)
if result.returncode == 0:
    path = result.stdout.strip().replace("cd '", "").strip("'")
    os.chdir(path)
    
    # 获取分支名
    branch = subprocess.run(['git', 'branch', '--show-current'],
                           capture_output=True, text=True).stdout.strip()
    print(f"📍 当前: {branch} | {path}")
```

## 明确回答用户

**用户**: "当前在哪个分支"

**Agent**: "当前在 feature-login 分支，目录是 /project-worktrees/alice_feature-login/"

**用户**: "我要切换到 payment 分支"

**Agent**: "已切换到 feature-payment 分支，新目录是 /project-worktrees/alice_feature-payment/"

## 安装

```bash
pip install git+https://github.com/Barber0/para-branch.git
```

## 命令

| 命令 | 说明 |
|------|------|
| `para-branch bind <项目> <分支>` | 在当前群聊创建分支环境 |
| `para-branch switch <分支>` | 切换到其他分支 |
| `para-branch info` | 查看当前分支和目录 |
| `para-branch list` | 列出所有分支（多用户） |
| `para-branch cd` | 输出 cd 命令 |
| `para-branch unbind` | 解除绑定 |
