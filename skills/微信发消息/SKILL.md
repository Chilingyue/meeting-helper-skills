---
name: 微信发消息
description: 用户在桌面微信里给某个群或个人发一条消息、不想自己动手点的时候使用。通过 Win32 截图/点击/剪贴板脚本操作微信客户端：恢复窗口 → 窗口截图量坐标 → 搜索会话 → 核对标题(群名带人数) → 输入内容(中文走剪贴板) → 点「发送」→ 截图确认气泡。同义说法：给群里发个消息、在XX群发一下、微信回他一句、发微信消息。
description_en: Send a WeChat message to a specific group or contact by driving the desktop client with window screenshots, CV template matching, clipboard paste and clicks. Use when the user asks to send a WeChat message without clicking themselves.
license: MIT
version: 1.0.0
agent_created: true
---

# 微信发消息

完整规范见 [`./微信发消息.md`](./微信发消息.md)。脚本在 `scripts/`，所有命令都在该目录下执行。

## 环境

Windows 10/11 + Python 3.8+，**只用标准库，不需要装任何包**。`python` 不在 PATH 就用 `py`。
`cvfind.py`（可选增强）额外需要 `opencv-python-headless numpy`，不装也能用整套流程。

## 铁律

1. **坐标 = 截图内坐标 + origin**。只截窗口（`grab.py`），窗口图 ≤1092px 不被缩放，量到多少点多少。全屏图会被缩放，禁止直接目测。
2. **点击/粘贴一律带 `--title 微信`**。它做命中测试 + 抢前台，不匹配就 exit 3 拒绝执行——abort 是保护，不是故障。
3. **中文/标点/表情只走 `paste.py`**。`type.py` 只认数字、字母、`-`、`.`，其它字符静默跳过；中文输入法激活时打字母还会被当拼音。
4. **发送前核对标题**：群是 `群名(人数)`，个人只有昵称。不符就停下重搜。
5. **发完必须截图验证**：绿色气泡内容逐字一致 + 输入框清空 + 发送按钮变灰。

## 五步

```bash
cd <本 skill 目录>/scripts

py win.py 微信                          # 1. 恢复并置前（托盘里的也能恢复）
py grab.py 微信 shot.png                # 2. 截窗口，记下打印的 origin
py key.py ctrl f                        # 3. Ctrl+F 聚焦搜索框（或点搜索框)
py paste.py "群名关键词" --title 微信     #    中文走粘贴；纯数字可用 type.py
py grab.py 微信 shot.png                #    截图确认下拉分组与目标行
py click.py <x> <y> --title 微信         #    点名字文字，别点头像

py click.py <输入框x> <输入框y> --title 微信
py paste.py "要发的内容" --replace --title 微信
py click.py <发送x> <发送y> --title 微信   # 4. 点「发送」，不要按 Enter
py grab.py 微信 after.png               # 5. 校验气泡 / 输入框 / 按钮
```

`grab.py` 会打印 `origin 952 1`，那么图上 `(185,72)` 就点 `(1137,73)`。

## 脚本

| 脚本 | 用途 |
| --- | --- |
| `winutil.py` / `pngio.py` | 共用底层，不直接调用 |
| `win.py 微信 [--list] [--wait N]` | 列出并置前（含托盘隐藏窗口）|
| `grab.py 微信 out.png [--scale N] [--screen]` | **截图首选**：1:1 PNG，打印 origin |
| `crop.py in.png x y w h out.png [scale]` | 裁一块放大看小字 / 做模板 |
| `click.py x y [--title 微信]` | 点击，带命中测试 |
| `paste.py "文本" [--replace] [--title 微信]` | 剪贴板粘贴，任意 Unicode |
| `type.py "文本"` / `--unicode` | 逐字输入 / 绕过输入法注入 |
| `key.py ctrl a` | 组合键（ctrl/shift/alt + 字母）|
| `diff.py a.png b.png` | 像素差，判断点击是否生效 |
| `cvfind.py --shot 微信 tpl/x.png` | 可选：模板匹配精确定位（需 opencv）|

## 最容易踩的五个坑

1. 窗口藏在托盘时 `IsWindowVisible=0`，但 `win.py 微信` 仍能找到——不用先判断可见性。
2. 点「进入微信」后界面消失 1~3 秒是隐藏创建，不是失败，等 2 秒再来。
3. 搜索框输入后框里看不到字是正常的，看下拉有没有出现「群聊/聊天记录」分组。
4. 「发送」灰着 = 输入框是空的，粘贴没生效，重点输入框再粘，别连点。
5. 换机器 / 换分辨率 / 换 DPI / 换主题 → 所有坐标和模板都要重测。

## 安全

消息文本一字不改；只发一处；内容或对象有歧义先问；认不准就重截图，禁止盲点重试。
