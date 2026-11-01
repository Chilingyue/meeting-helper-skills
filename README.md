# meeting-helper-skills

两个 Windows 桌面 Agent Skill：**在微信里给指定群或个人发消息**、**自动进腾讯会议并闭麦关摄像头**。

靠截屏 + 点击 + 键盘操作真实客户端窗口，不需要任何官方 API、不需要申请权限、不需要 pip install。适用于任何支持 `SKILL.md` 的 Agent（Claude Code / Codex / Cursor / WorkBuddy …）。

## 安装

```bash
npx skills add Chilingyue/meeting-helper-skills --skill wechat-send
```

不指定 `--skill` 会交互选择；两个都装用 `--skill '*'`。装到指定客户端加 `-a claude-code` 这类参数，全局安装加 `-g`。

客户端读固定目录、`npx` 认不出来时（例如 WorkBuddy 读 `~/.workbuddy/skills/`），直接拷目录：

```bash
git clone --depth 1 https://github.com/Chilingyue/meeting-helper-skills.git /tmp/mhs \
  && cp -r /tmp/mhs/skills/wechat-send /tmp/mhs/skills/meeting-auto-join ~/.workbuddy/skills/
```

| Skill | 做什么 | 怎么说 |
| --- | --- | --- |
| `wechat-send`（微信发消息） | 恢复窗口 → 搜索会话 → 核对标题 → 输入 → 点发送 → 截图验证 | "在 3-204 群发个 1"、"微信回他我七点到" |
| `meeting-auto-join`（预约自动入会） | 进会议 → 取消勾选入会开麦/开摄像头 → 确认已静音、摄像头关 | "帮我进这个会 123-456-789"、"进会并静音" |

每个目录自包含：`SKILL.md`（Agent 入口）、`GUIDE.md`（完整规范与踩过的坑）、`scripts/`。

## 环境

Windows 10/11 + Python 3.8+（只用标准库；`opencv` 仅模板匹配 `cvfind.py` 可选）。`python` 不在 PATH 用 `py`。macOS / Linux 用不了，全是 Win32 API。

## 换机器必须重新校准

仓库里没有硬编码坐标，坐标都是运行时从截图量出来的，但**量出来的值跟你机器有关**：

| 变量 | 影响 |
| --- | --- |
| 分辨率与缩放（100% / 125% / 150%） | 窗口尺寸、控件位置全变 |
| 客户端版本与主题（浅色/深色、字号） | 按钮位置和颜色变，`scripts/tpl/` 里的示例模板失效 |
| 窗口是否最大化、停在哪一侧 | origin 与相对偏移变 |

所以正确用法是**每一步基于最新截图重新量**，别复述文档里的数字（都是脱敏示例）。模板失效就用 `crop.py` 重裁一张，`GUIDE.md` 有现成命令。

## 免责声明

这些脚本会真实操作鼠标和键盘。用前关掉其它敏感窗口；发消息类操作务必人工确认对象与内容（脚本会先核对会话标题、`--title` 命中测试不通过就拒绝点击，但机器判断不是万无一失）。作者不对误发、误操作造成的后果负责。

## License

MIT，见 [LICENSE](LICENSE)。
