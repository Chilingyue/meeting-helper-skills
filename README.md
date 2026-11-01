# meeting-helper-skills

[![skills.sh](https://skills.sh/b/Chilingyue/meeting-helper-skills)](https://skills.sh/Chilingyue/meeting-helper-skills)

两个 Windows 桌面 Agent Skill：**在微信里给指定群或个人发消息**、**自动进腾讯会议并闭麦关摄像头**。

靠截屏 + 点击 + 键盘操作真实客户端窗口，不需要官方 API、不需要申请权限、不需要 pip install。适用于任何支持 `SKILL.md` 的 Agent（Claude Code / Codex / Cursor / WorkBuddy …）。

| Skill | 做什么 | 怎么说 |
| --- | --- | --- |
| `wechat-send`（微信发消息） | 恢复窗口 → 搜索会话 → 核对标题 → 输入 → 点发送 → 截图验证 | "在 3-204 群发个 1"、"微信回他我七点到" |
| `meeting-auto-join`（预约自动入会） | 进会议 → 取消勾选入会开麦/开摄像头 → 确认已静音、摄像头关 | "帮我进这个会 123-456-789"、"进会并静音" |

## 安装

三种方式，任选一种。装完重启客户端即可生效。

### 方式一：npx（推荐，一行）

需要 Node.js 22+。

```bash
# 两个都装
npx skills add Chilingyue/meeting-helper-skills --skill '*'

# 只装微信发消息
npx skills add Chilingyue/meeting-helper-skills --skill wechat-send

# 只装腾讯会议入会
npx skills add Chilingyue/meeting-helper-skills --skill meeting-auto-join
```

加 `-g` 装到全局（默认装当前项目），加 `-a claude-code` 指定客户端，`-y` 跳过确认。

### 方式二：git clone + 复制（不用 npx）

PowerShell：

```powershell
git clone --depth 1 https://github.com/Chilingyue/meeting-helper-skills.git "$env:TEMP\mhs"
Copy-Item "$env:TEMP\mhs\skills\*" "$env:USERPROFILE\.workbuddy\skills\" -Recurse -Force
```

Git Bash / macOS：

```bash
git clone --depth 1 https://github.com/Chilingyue/meeting-helper-skills.git /tmp/mhs \
  && cp -r /tmp/mhs/skills/* ~/.workbuddy/skills/
```

只想要一个 skill 就把 `skills\*` 换成 `skills\wechat-send` 或 `skills\meeting-auto-join`。

### 方式三：下载压缩包（最简单，连 git 都不用）

1. 点下面链接直接下载：
   - 微信发消息 → [wechat-send.zip](https://github.com/Chilingyue/meeting-helper-skills/releases/latest/download/wechat-send.zip)
   - 腾讯会议入会 → [meeting-auto-join.zip](https://github.com/Chilingyue/meeting-helper-skills/releases/latest/download/meeting-auto-join.zip)
2. 解压，得到一个同名文件夹（例如 `wechat-send`）。
3. 整个文件夹拖进 skills 目录：
   - WorkBuddy：`C:\Users\<你>\.workbuddy\skills\`
   - Claude Code：`C:\Users\<你>\.claude\skills\`
   - 其它客户端：它自己文档里写的 skills 目录
4. 重启客户端。

文件夹名不要改，`SKILL.md` 里的 `name` 和目录名是一一对应的。

## 配合定时任务：预约发消息 / 预约入会

如果你的 Agent 带定时（cron / 定时任务 / 到点唤醒）能力，这两个 skill 可以拼成预约执行：

| 想要的效果 | 定时任务里让它做的事 |
| --- | --- |
| 预约自动发消息 | 提前恢复微信、打开目标会话、把内容粘进输入框；准点点「发送」 |
| 预约自动进会议 | 提前启动客户端、进会议、取消勾选开麦/开摄像头；准点到点做最后确认 |

**建议提前 5 分钟启动，准点到点只做最后一步。** 原因很实在：这套流程走的是截屏 + 点击，每一步都要耗时间——客户端冷启动、登录态检查、窗口被抢前台、截图定位、点击后复核；遇到会议号输错、窗口没抢到前台还得重试一轮。如果压到准点才启动，等它跑完，会已经开了几分钟，消息也早该发了。

所以把一次预约拆成两段：

- **预热段（提前 5 分钟）**：启动/恢复窗口 → 核对已登录 → 搜到目标会话或会议 → 取消开麦、关摄像头 → 内容粘到输入框（不发送）
- **交付段（准点）**：只剩一个动作——点「发送」，或在会议里确认自己已在会中且静音

这样中途卡一次还有时间补救，准点那一下误差最小。

给 Agent 的 prompt 可以这么写（把时间和对象换掉）：

> 明天 09:55 开始，用 wechat-send 给「XXX 群」发「今天十点开会，别迟到」。09:55 先把微信窗口恢复、会话打开、内容粘好，10:00 再点发送。

> 明天 14:55 开始，用 meeting-auto-join 进会议 123-456-789。提前进去并确保麦克风静音、摄像头关闭，15:00 检查一次仍在会中、仍是静音状态。

注意：定时任务跑的时候机器得醒着、客户端得已登录，锁屏状态下截屏会拿到锁屏画面。建议提前测一次同样的流程，确认这台机器的耗时，再决定提前几分钟。

## 环境

Windows 10/11 + Python 3.8+（只用标准库；`opencv` 仅模板匹配 `cvfind.py` 可选）。`python` 不在 PATH 就用 `py`。macOS / Linux 用不了，全是 Win32 API。

## 换机器必须重新校准

仓库里没有硬编码坐标，坐标都是运行时从截图量出来的，但**量出来的值跟你机器有关**：

| 变量 | 影响 |
| --- | --- |
| 分辨率与缩放（100% / 125% / 150%） | 窗口尺寸、控件位置全变 |
| 客户端版本与主题（浅色/深色、字号） | 按钮位置和颜色变，`scripts/tpl/` 里的示例模板失效 |
| 窗口是否最大化、停在哪一侧 | origin 与相对偏移变 |

所以正确用法是**每一步基于最新截图重新量**，别复述文档里的数字（都是脱敏示例）。模板失效就用 `crop.py` 重裁一张，`GUIDE.md` 里有现成命令。

## 免责声明

这些脚本会真实操作鼠标和键盘。用前关掉其它敏感窗口；发消息类操作务必人工确认对象与内容（脚本会先核对会话标题，`--title` 命中测试不通过就拒绝点击，但机器判断不是万无一失）。作者不对误发、误操作造成的后果负责。

## License

MIT，见 [LICENSE](LICENSE)。
