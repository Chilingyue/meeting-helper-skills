---
name: meeting-auto-join
description: 用户转发腾讯会议邀请、只给了会议号、或要求"帮我入会/打开那个会"并希望自动闭麦关摄像头时使用。通过 Win32 截图/点击/键盘脚本操作腾讯会议客户端：置前 → 进入会议(点待开始会议行，或输入会议号) → 核对会议设置(取消勾选入会开摄像头/开麦克风) → 选电脑音频 → 校验已闭麦且摄像头关闭。同义说法：直接进会、加入会议、打开会议、入会并静音、腾讯会议自动入会、自动进会议室、自动闭麦关摄像头、会议定时入会。
description_en: Join a Tencent Meeting (WeMeet) invitation on the desktop client and leave microphone muted and camera off, driven by window screenshots, clicks and hotkeys. Keywords — tencent meeting auto join, wemeet automation, auto mute microphone, turn off camera, scheduled meeting join.
license: MIT
version: 1.0.2
agent_created: true
---

# 预约自动入会（`meeting-auto-join`）

完整规范见 [`GUIDE.md`](./GUIDE.md)。脚本在 `scripts/`，命令都在该目录下执行。

## 环境

Windows 10/11 + Python 3.8+，**只用标准库**。客户端进程 `wemeetapp.exe`。`python` 不在 PATH 就用 `py`。

## 铁律

1. **静音/关视频按优先级来，不可颠倒**：入会前在表单里取消勾选 → 进会后点工具栏按钮 → 实在不行才用快捷键 `Alt+V` / `Alt+M`（且必须会议窗口在前台）。
2. **表单默认值不可信**：「入会开启摄像头」「入会开启麦克风」同机两次实测都不一样，必须逐项核对并取消勾选。
3. **坐标每步重算**：弹窗每次点击都会挪位，点空就重截重算，不要连点。
4. **做完必须截图检查**：显示「解除静音」「开启视频」才是已闭麦 + 已关摄像头（反向判读）。
5. **退出用「离开会议」，绝不用「结束会议」**（会解散别人的会）。

## 流程

```bash
cd <本 skill 目录>/scripts

py win.py 腾讯会议                       # 1. 置前（托盘里的也能恢复）
# 没窗口就先拉起：cmd //c start "" "wemeet://page/join?meeting_code=123456789"
# 注意：URL 不会预填会议号，仍要手动输入

py grab.py 腾讯会议 s1.png               # 2. 截主界面，量「加入会议」坐标
py click.py <x> <y> --title 腾讯会议

py grab.py 腾讯会议 s2.png               # 3. 弹窗出现后重新量坐标
py click.py <输入框x> <输入框y> --title 腾讯会议
py type.py 123456789                     #    会议号纯数字，不受输入法影响

py crop.py s2.png <表单设置区> 4          # 4. 放大核对「入会开启摄像头/麦克风」未勾选
py click.py <勾选框x> <勾选框y> --title 腾讯会议

py click.py <加入会议x> <加入会议y>       # 5. 按钮由灰变蓝才点
py grab.py 腾讯会议 s3.png               # 6. 进会后悬停底部 2s 再截，确认状态
```

## 脚本

| 脚本 | 用途 |
| --- | --- |
| `winutil.py` / `pngio.py` | 共用底层 |
| `win.py 腾讯会议` / `win.py 快速会议` | 置前；会中标题不含「腾讯会议」，要按会议名找 |
| `grab.py 腾讯会议 out.png` | 窗口截图，1:1，打印 origin |
| `crop.py in.png x y w h out.png [scale]` | 放大看 16px 的复选框 / 小按钮 |
| `click.py x y --title 腾讯会议` | 点击，带命中测试 |
| `type.py 123456789` | 输入会议号 |
| `key.py alt v` / `key.py alt m` | 兜底快捷键：开/关视频、静音/解除静音 |
| `paste.py "文本"` | 需要输入中文时用 |
| `diff.py a.png b.png` | 判断点击后状态是否变了 |

## 收尾判读

| 看到 | 含义 |
| --- | --- |
| 「解除静音」+ 红斜杠 | 麦克风已关 ✔ |
| 「开启视频」+ 红斜杠 | 摄像头已关 ✔ |
| 「静音」/「停止视频」无斜杠 | 还开着 ✘ |

会中工具栏会自动隐藏：截图前把鼠标移到窗口底部悬停 1.5~2 秒，否则截到空白。
`py -c "import ctypes; ctypes.windll.user32.SetCursorPos(960, 1040)"`

## 预约入会（有定时能力的 Agent）

要被定时任务调用时，**提前 5 分钟启动，准点到点只做最后确认**：先启动客户端、输会议号进会、取消勾选开麦/开摄像头并校验静音，到点再确认仍在会中且麦克风、摄像头状态正确。冷启动、登录、抢前台都可能重试，压到准点才跑会迟到。

## 安全

只操作本地客户端窗口；不替用户开麦、开摄像头、共享屏幕；不改会议信息；不点「结束会议」。
报告时说清：进了哪场会、是否已闭麦、是否已关摄像头。
