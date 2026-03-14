# para-branch

不同群聊，自动隔离，同时开发。

## 安装

```bash
pip install git+https://github.com/Barber0/para-branch.git
```

## 用法

```bash
# 告诉系统：我要在这个群聊开发 xxx 功能
para-branch bind ~/myproject feature-xxx

# 进入开发目录
cd $(para-branch cd)

# 换功能开发
para-branch switch feature-yyy
```

## 自然语言

直接说：
- "我要在这个群聊开发登录功能"
- "切换到支付功能"
- "我现在在哪个功能上"
- "列出这个项目的所有开发环境"

Agent 会自动处理，不需要知道底层细节。

## 原理（可选了解）

每个群聊绑定到 Git 仓库的独立目录，互不干扰。Git 负责同步代码，我们负责隔离环境。

## 许可证

MIT - [Zilin Fang](https://github.com/Barber0)
