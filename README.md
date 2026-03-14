# paraclaw-b0

让不同聊天会话各自工作在独立的 Git 分支上。

## 一句话说明

你在群聊 A 开发登录功能，群聊 B 开发支付功能，两个群聊同时操作同一个代码仓库，却互不干扰。

## 安装到 OpenClaw

```bash
# 在 OpenClaw 环境中安装
clawhub install paraclaw-b0

# 或手动安装到 skills 目录
cd ~/.openclaw/skills
git clone https://github.com/Barber0/paraclaw-b0.git
```

## 怎么用

```bash
# 在当前群聊绑定分支
worktree-session bind ~/myproject feature-login

# 进入工作目录
cd $(worktree-session cd)

# 现在所有操作都在 feature-login 分支的独立目录里
```

另一个群聊：
```bash
worktree-session bind ~/myproject feature-payment
cd $(worktree-session cd)
# 现在操作的是 feature-payment 分支，和群聊 A 完全隔离
```

## 优势

| 场景 | 不用 paraclaw-b0 | 用 paraclaw-b0 |
|------|------------------|----------------|
| 多群聊协作 | 频繁切换分支，容易冲突 | 各聊各的，完全隔离 |
| 代码安全 | 不小心改错分支 | 每个群聊锁定自己的分支 |
| 上下文保持 | 重新找文件位置 | 直接 `cd $(worktree-session cd)` 进入 |

## 简单原理

Git Worktree 允许一个仓库有多个独立工作目录，每个目录绑定一个分支。

paraclaw-b0 给每个聊天会话分配一个 Worktree，Session A 永远操作目录 A，Session B 永远操作目录 B。

```
Session A ──→ Worktree A (feature-login)
Session B ──→ Worktree B (feature-payment)
     ↑              ↓
   群聊消息    独立文件系统
```

## 许可证

MIT - [Zilin Fang](https://github.com/Barber0)
