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
              "bins": ["worktree-session"],
              "label": "Install paraclaw-b0 via pip"
            }
          ]
      }
  }
---

# paraclaw-b0

让不同的聊天会话各自工作在独立的 Git Worktree 中，实现真正的并行分支开发。

## 核心概念

```
群聊 A ──→ Worktree A (feature-auth)     独立文件系统
群聊 B ──→ Worktree B (feature-payment)  独立文件系统  
私聊   ──→ Worktree C (bugfix-ui)        独立文件系统
```

- **Session**: 聊天上下文（飞书群聊、私聊、Discord 频道等）
- **Worktree**: Git 的独立工作目录，每个 worktree 对应一个分支
- **Binding**: 将 Session 永久关联到某个 worktree，后续操作自动在该目录执行

## 快速开始

### 1. 在当前群聊绑定分支

```bash
# 在当前群聊创建并绑定到 feature-login 分支
worktree-session bind /path/to/repo feature-login
```

输出示例：
```
[创建分支] feature-login
[创建 Worktree] /home/user/repo-worktrees/feature-login
[绑定成功]
  Session: feishu-group-xxx
  分支: feature-login
  Worktree: /home/user/repo-worktrees/feature-login
  仓库: /home/user/repo
```

### 2. 查看当前绑定

```bash
worktree-session info
```

### 3. 切换到 worktree 目录工作

```bash
# 获取 cd 命令
cd $(worktree-session cd)
```

### 4. 在另一个群聊绑定另一个分支

在群聊 B 中：
```bash
worktree-session bind /path/to/repo feature-payment
```

现在两个群聊完全独立，各自在自己的分支上工作！

## 完整使用流程

### 场景：同时开发三个功能

**群聊 A - 认证功能：**
```bash
# 绑定
worktree-session bind ~/projects/myapp feature-auth

# 之后所有操作都在 ~/projects/myapp-worktrees/feature-auth 中
cd $(worktree-session cd)
git status  # 在 feature-auth 分支
code .      # 用 VS Code 打开
```

**群聊 B - 支付功能：**
```bash
worktree-session bind ~/projects/myapp feature-payment
cd $(worktree-session cd)
git status  # 在 feature-payment 分支
```

**群聊 C - UI 修复：**
```bash
worktree-session bind ~/projects/myapp bugfix-ui
cd $(worktree-session cd)
git status  # 在 bugfix-ui 分支
```

### 切换分支（在同一群聊）

```bash
# 从 feature-auth 切换到 feature-oauth
worktree-session switch feature-oauth
```

### 查看所有绑定

```bash
worktree-session list
```

输出：
```
[所有绑定关系] 共 3 个

  Session: feishu-group-xxx
    分支: feature-auth
    Worktree: /home/user/projects/myapp-worktrees/feature-auth

  Session: feishu-group-yyy
    分支: feature-payment
    Worktree: /home/user/projects/myapp-worktrees/feature-payment

  Session: feishu-dm-zzz
    分支: bugfix-ui
    Worktree: /home/user/projects/myapp-worktrees/bugfix-ui
```

### 解除绑定

```bash
worktree-session unbind
```

## 快捷别名设置

添加到 `~/.bashrc` 或 `~/.zshrc`：

```bash
# Worktree Session Manager 快捷命令
alias wts='worktree-session'
alias wts-bind='wts bind'
alias wts-info='wts info'
alias wts-list='wts list'
alias wts-switch='wts switch'
alias wts-cd='cd "$(wts cd 2>/dev/null || echo .)"'

# 快速进入当前 session 的 worktree
worktree-cd() {
    local dir=$(wts cd 2>/dev/null)
    if [ -n "$dir" ]; then
        cd "$dir"
        echo "已进入: $dir"
        git status
    else
        echo "当前 session 未绑定 worktree"
        echo "使用: wts-bind <repo> <branch>"
    fi
}
```

## 与 OpenClaw 集成

当 skill 检测到当前 session 已绑定 worktree 时，可以：

1. **自动切换目录**：执行命令前自动 `cd` 到 worktree 目录
2. **显示上下文**：每次回复前显示当前分支信息
3. **隔离操作**：确保文件操作只在绑定的 worktree 中进行

### 示例：在 Skill 中使用

```python
import subprocess

# 获取当前 session 的 worktree
result = subprocess.run(
    ['worktree-session', 'cd'],
    capture_output=True, text=True
)

if result.returncode == 0:
    worktree_path = result.stdout.strip()
    # 在 worktree 中执行操作
    subprocess.run(['git', '-C', worktree_path, 'status'])
else:
    print("当前 session 未绑定 worktree")
```

## 技术细节

### 存储位置

- 映射文件：`~/.openclaw/worktree-sessions.json`
- Worktrees：默认在 `{repo-parent}/{repo-name}-worktrees/{branch}/`

### Session ID 识别

自动尝试以下环境变量（按优先级）：
1. `OPENCLAW_SESSION_ID`
2. `SESSION_KEY`
3. `CHAT_ID`
4. 默认值: `default`

## 最佳实践

1. **命名规范**：分支名使用 `feature-xxx` 或 `bugfix-xxx`
2. **及时清理**：功能合并后手动删除不需要的 worktree
3. **不要嵌套**：worktree 目录不要放在原仓库内部
4. **环境同步**：每个 worktree 需要独立安装依赖

## 对比其他方案

| 方式 | 优点 | 缺点 |
|------|------|------|
| 简单分支切换 | 快速 | 文件互相覆盖，无法并行 |
| **Worktree Session** | 真正的并行，完全隔离 | 需要更多磁盘空间 |
| 多次克隆 | 完全隔离 | 浪费空间，历史不同步 |

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 作者

Zilin Fang - https://github.com/Barber0
