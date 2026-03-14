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

English | [中文](#中文文档)

## 🎯 核心概念

```
Chat A ──→ Worktree A (feature-auth)      独立文件系统
Chat B ──→ Worktree B (feature-payment)   独立文件系统  
DM     ──→ Worktree C (bugfix-ui)         独立文件系统
```

- **Session**: 聊天上下文（飞书群聊、私聊、Discord 频道等）
- **Worktree**: Git 的独立工作目录，每个 worktree 对应一个分支
- **Binding**: 将 Session 永久关联到某个 worktree，后续操作自动在该目录执行

## ✨ 功能特性

- 🔗 **Session-Worktree 绑定** - 每个聊天上下文独立绑定到一个 Git 分支
- 🌿 **自动分支管理** - 分支不存在时自动创建，worktree 已存在时复用
- 🔄 **无缝切换** - 在同一 Session 内快速切换不同分支
- 📊 **绑定管理** - 查看、列出、解除所有绑定关系
- 🛡️ **数据安全** - 不会自动删除 worktree，防止数据丢失
- 🎨 **多平台支持** - 支持飞书、Discord、Slack 等多种聊天平台
- 💬 **自然语言支持** - 可以直接说"在这个群聊绑定 feature-xxx 分支"

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/Barber0/paraclaw-b0.git
cd paraclaw-b0

# 安装
pip install -e .

# 或者直接用脚本
chmod +x scripts/worktree-session
sudo ln -s $(pwd)/scripts/worktree-session /usr/local/bin/
```

### 基础用法

```bash
# 1. 在当前聊天绑定到 feature-login 分支
worktree-session bind /path/to/repo feature-login

# 2. 查看当前绑定
worktree-session info

# 3. 进入 worktree 目录
cd $(worktree-session cd)

# 4. 在另一个聊天绑定另一个分支
worktree-session bind /path/to/repo feature-payment
```

### 💬 自然语言使用

你也可以直接说：
- "在这个群聊绑定 feature-xxx 分支"
- "我要在这个群聊开发支付功能"
- "切换到 bugfix 分支"
- "查看当前绑定的 worktree"

## 📖 使用示例

### 场景：同时开发三个功能

**群聊 A - 认证功能：**
```bash
worktree-session bind ~/projects/myapp feature-auth
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

### 常用命令

| 命令 | 说明 |
|------|------|
| `bind <repo> <branch>` | 绑定当前 Session 到指定分支 |
| `info` | 查看当前 Session 的绑定信息 |
| `list` | 列出所有绑定关系 |
| `switch <branch>` | 切换到新分支 |
| `unbind` | 解除当前 Session 的绑定 |
| `cd` | 获取进入 worktree 的 cd 命令 |

## ⚡ 快捷别名

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

## ⚙️ 与 OpenClaw 集成

当与 [OpenClaw](https://openclaw.ai) 配合使用时：

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

## 🛠️ 技术细节

### 存储位置

- 映射文件：`~/.openclaw/worktree-sessions.json`
- Worktrees：`{repo-parent}/{repo-name}-worktrees/{branch}/`

### Session ID 识别

自动尝试以下环境变量（按优先级）：
1. `OPENCLAW_SESSION_ID`
2. `SESSION_KEY`
3. `CHAT_ID`
4. 默认值: `default`

### 分支创建策略

- 如果分支不存在，自动创建
- 如果 worktree 已存在，直接复用
- 不会自动删除 worktree（防止数据丢失）

## 🐛 故障排除

### 问题：绑定后无法找到 worktree

```bash
# 检查绑定信息
worktree-session info

# 手动查看映射文件
cat ~/.openclaw/worktree-sessions.json
```

### 问题：Session ID 不正确

```bash
# 手动指定 session ID 绑定
worktree-session bind --session "your-session-id" /path/to/repo branch-name
```

### 问题：worktree 创建失败

```bash
# 检查原仓库是否有未提交的更改
cd /path/to/repo
git status

# 清理后重试
git worktree prune
```

## 💡 最佳实践

1. **命名规范**：分支名使用 `feature-xxx` 或 `bugfix-xxx`，一目了然
2. **及时清理**：功能合并后，手动删除不需要的 worktree 目录
3. **不要嵌套**：worktree 目录不要放在原仓库内部
4. **环境同步**：每个 worktree 需要独立安装依赖（如 `npm install`）

## 🆚 对比其他方案

| 方式 | 优点 | 缺点 |
|------|------|------|
| 简单分支切换 | 快速 | 文件互相覆盖，无法并行 |
| **Worktree Session** | 真正的并行，完全隔离 | 需要更多磁盘空间 |
| 多次克隆 | 完全隔离 | 浪费空间，历史不同步 |

Worktree 是最佳平衡点：共享 git 历史，独立工作目录。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

Created by [Zilin Fang](https://github.com/Barber0)
