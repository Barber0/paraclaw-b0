# paraclaw-b0

让不同聊天会话各自工作在独立的 Git 分支上。

## 一句话说明

群聊 A 开发登录功能，群聊 B 开发支付功能，同时操作同一个代码仓库，互不干扰。

## 安装

```bash
pip install git+https://github.com/Barber0/paraclaw-b0.git
```

## 使用

```bash
# 绑定当前群聊到分支
paraclaw bind ~/myproject feature-login

# 查看当前绑定
paraclaw info

# 进入工作目录
cd $(paraclaw cd)

# 切换到新分支
paraclaw switch feature-payment

# 查看所有绑定（多用户时有用）
paraclaw list
```

## 多用户支持

同一台机器上多个用户/平台自动隔离，互相可见但不冲突：

```bash
# Alice（飞书）
paraclaw bind ~/project feature-auth

# Bob（Discord，同一台机器）
paraclaw bind ~/project feature-payment

# 查看所有人的绑定
paraclaw list
```

## 许可证

MIT - [Zilin Fang](https://github.com/Barber0)
