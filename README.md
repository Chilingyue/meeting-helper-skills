# meeting-helper-skills

用**截屏 + 点击 + 键盘**驱动 Windows 桌面客户端的两个 AI Agent Skill：自动进腾讯会议（并顺手闭麦、关摄像头）、在微信里给指定群或个人发消息。

不依赖任何官方 API、不申请任何权限、不装第三方库——脚本全部用 Python 标准库 + Win32 API 写成。适用于 Claude Code / WorkBuddy 这类支持 `SKILL.md` 的 Agent。

> 一句话原理：把目标窗口单独截成 1:1 的 PNG，让 Agent 在图上读到"发送按钮在 (904, 987)"，加上窗口原点就是屏幕坐标，然后点它。因为窗口图宽度通常小于看图工具的缩放阈值，图上的像素就是屏幕上的像素，不需要换算。

---

## 包含的 Skill

| Skill | 做什么 | 触发示例 |
| --- | --- | --- |
| `预约自动入会` | 打开腾讯会议客户端 → 进入指定会议 → 确认麦克风静音、摄像头关闭 | "帮我进这个会 123-456-789"、"进会并静音" |
| `微信发消息` | 恢复微信窗口 → 搜索会话 → 核对标题 → 输入并发送 → 截图验证 | "在 XX 群发个 1"、"微信回他一句我七点到" |

每个目录都是自包含的：`SKILL.md`（给 Agent 的精简指令）+ 完整规范 + `scripts/`。

---

## 安装

### 方式一：一条命令（Windows PowerShell）

```powershell
git clone https://github.com/Chilingyue/meeting-helper-skills.git
cd meeting-helper-skills
powershell -ExecutionPolicy Bypass -File install.ps1
```

`install.ps1` 会把 `skills\*` 复制到 `%USERPROFILE%\.workbuddy\skills\`，已存在时先备份成 `.bak-时间戳`。装到别的客户端就指定目标目录：

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -Dest "$env:USERPROFILE\.claude\skills"
```

Git Bash 用户可以用 `./install.sh`，参数是目标目录。

### 方式二：手动复制

把 `skills\微信发消息`、`skills\预约自动入会` 两个目录整个拷到：

```
C:\Users\<你>\.workbuddy\skills\
```

复制完重启 Agent 客户端即可。目录名不用改，`SKILL.md` 里的 `name` 字段就是技能名。

### 方式三：只用脚本，不装 Skill

直接把 `skills\微信发消息\scripts\` 当成一组命令行小工具用，见下面的「手动使用」。

---

## 环境要求

| 项目 | 要求 |
| --- | --- |
| 操作系统 | **Windows 10 / 11**（全是 Win32 API，macOS / Linux 不可用） |
| Python | 3.8+，**只用标准库，无需 pip install** |
| 可选 | `opencv-python-headless` + `numpy`，仅 `cvfind.py` 模板匹配需要 |

`python` 不在 PATH 时用 Windows 自带的 `py` 启动器，两者等价。

---

## 快速验证

```powershell
cd skills\微信发消息\scripts

py win.py 微信                 # 能找到窗口并置前？
py grab.py 微信 shot.png       # 截出 1:1 图，打印 origin
py crop.py shot.png 0 0 400 200 zoom.png 2   # 放大左上角，看看坐标是否好读
```

`grab.py` 的输出形如：

```
window: 1234567 '微信' visible rect (960, 1, 957, 1029) dpi 1.25
saved shot.png 957x1029 origin 960 1 | method print
```

那么截图上的 `(185, 72)` 对应的屏幕坐标就是 `(960+185, 1+72) = (1145, 73)`。

---

## ⚠️ 换机器必须重新校准坐标

这是使用前最重要的一段。**仓库里没有任何硬编码的坐标**——所有坐标都是运行时从截图量出来的，但"量出来的值"依赖你的环境：

| 变量 | 影响 |
| --- | --- |
| 屏幕分辨率与缩放（100% / 125% / 150%） | 窗口尺寸与控件位置全变 |
| 客户端版本与主题（浅色/深色、字号） | 按钮位置、颜色变，模板失效 |
| 窗口是否最大化、被拖到哪一侧 | origin 与相对偏移变 |

所以正确姿势是：**每一步都基于最新截图重新量**，不要复述文档里的示例数字（文档里的坐标都是脱敏示例，在本机之外无效）。

`scripts/tpl/example_button.png` 同样是示例模板，换主题后必须用 `crop.py` 重新裁一个。

用模板匹配可以免去肉眼估坐标：

```powershell
py crop.py shot.png 872 972 62 30 tpl/my_send.png     # 一次性：裁模板
py cvfind.py --shot 微信 tpl/my_send.png --top 3      # 每次：找它，返回精确中心
py cvfind.py --shot 微信 tpl/my_send.png --click --title 微信
```

---

## 手动使用（当命令行工具）

| 脚本 | 用途 |
| --- | --- |
| `win.py <标题片段> [--list] [--wait N]` | 找窗口（含托盘隐藏窗口）并置前 |
| `grab.py <标题片段>/full out.png [--scale N] [--screen]` | 窗口截图 → 1:1 PNG，打印 origin |
| `crop.py in.png x y w h out.png [scale]` | 裁剪 / 整数放大 |
| `click.py x y [--double] [--title 片段]` | 点击；带 `--title` 时先做命中测试，点不到目标就拒绝 |
| `paste.py "文本" [--replace] [--title 片段]` | 剪贴板粘贴，任意 Unicode |
| `type.py "文本"` / `type.py --unicode "文本"` | 逐字输入 / 绕过输入法注入 |
| `key.py ctrl a` / `key.py alt v` | 单键与组合键 |
| `diff.py a.png b.png` | 像素差对比，判断点击是否生效 |
| `cvfind.py --shot ...` | 模板匹配定位（可选，需 opencv） |

示例——把微信窗口里某个坐标点一下：

```powershell
py win.py 微信 && py grab.py 微信 s.png && py click.py 1145 748 --title 微信
```

`--title` 是安全闸：它会用 `WindowFromPoint` 问 Windows「这一点最上层是谁」，不是目标窗口就尝试抢回前台，仍不对就退出码 3 **什么都不点**。键击只发给前台窗口，点击只命中最上层窗口，少了这道闸很容易点到/粘到别的程序里。

---

## 常见问题

**截出来一片空白 / 全是黑的？**
`grab.py` 默认用 `PrintWindow` 让窗口自己渲染，被遮挡也能截到；个别 GPU 渲染的程序会返回空白，此时脚本自动回退到屏幕抓取。仍不行就加 `--screen`（要求窗口在前台），或先 `py win.py <标题>` 置前再截。

**点不中？**
先确认三件事：截图是不是最新的、坐标有没有加 origin、那个点是不是被别的窗口盖着。用 `py crop.py` 放大看目标，或直接上 `cvfind.py`。

**能不能不装 opencv？**
能。截图、裁剪、点击、粘贴、状态校验全都只用标准库，opencv 只用于模板匹配这一项可选增强。

**为什么不干脆用 UI Automation（uiautomation / pywinauto）？**
微信 4.x 是 Qt 自绘（`Qt51514QWindowIcon`），整棵控件树只有一个渲染面板，拿不到搜索框和按钮；腾讯会议同类的自绘控件也取不到有效矩形。这条路实测走不通，所以退回"截图 + 像素坐标"这条更笨但更通用的路。

**会不会误发消息？**
发送动作永远是最后一步、且必须先截图核对会话标题（群名带人数）。`--title` 闸 + 发送前确认，是为了把"发错人"的概率压到最低。文档里也写死了：内容或对象有歧义必须先问用户。

---

## 目录结构

```
meeting-helper-skills/
├── skills/
│   ├── 微信发消息/
│   │   ├── SKILL.md            # 给 Agent 的入口
│   │   ├── 微信发消息.md        # 完整规范（流程、坑、校验、安全约束）
│   │   └── scripts/            # 12 个脚本 + tpl/ 示例模板
│   └── 预约自动入会/
│       ├── SKILL.md
│       ├── 预约自动入会.md
│       └── scripts/
├── tools/sync_common.py        # 维护用：两个 skill 的公共脚本保持同步
├── install.ps1
└── LICENSE
```

两个 skill 的 `scripts/` 里有一组完全相同的公共文件（`winutil.py`、`pngio.py`、`win.py`、`grab.py`、`crop.py`、`click.py`、`key.py`、`type.py`、`paste.py`、`diff.py`）。这样做是为了让每个 skill 目录自包含、可单独拷走——代价是改了公共脚本要跑一次 `python tools/sync_common.py`。

---

## 免责声明

这些脚本会真实地操作你的鼠标和键盘。请在使用前关闭其它敏感窗口，发消息类操作务必人工确认对象与内容。作者不对误发、误操作造成的任何后果负责。

## License

MIT，见 [LICENSE](LICENSE)。
