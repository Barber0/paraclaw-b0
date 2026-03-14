# para-branch

不同群聊，不同分支，同时开发。

## 安装

```bash
pip install git+https://github.com/Barber0/para-branch.git
```

## 用法

```bash
# 在当前群聊创建 feature-xxx 分支的开发环境
para-branch bind ~/myproject feature-xxx

# 进入开发目录
cd $(para-branch cd)

# 查看当前在哪个分支
git branch  # 或 para-branch info

# 切换到其他分支开发
para-branch switch feature-yyy

# 查看所有人在开发哪些分支
para-branch list
```

## 自然语言

可以直接说：
- "我要在这个群聊开发 feature-login 分支"
- "当前在哪个分支"
- "切换到 feature-payment 分支"
- "列出所有分支"
- "我现在编辑的是哪个目录"

Agent 会自动处理。

## 原理

每个群聊绑定到 Git 仓库的独立工作目录，各自在不同的分支上，互不干扰。

## 许可证

MIT - [Zilin Fang](https://github.com/Barber0)
