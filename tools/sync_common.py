"""维护脚本：把公共脚本从「微信发消息」同步到「预约自动入会」。

两个 skill 目录是自包含的（可单独拷走），代价是公共脚本各存一份。
改了公共文件后跑一次这个脚本，避免两边不一致：

    python tools/sync_common.py          # 同步
    python tools/sync_common.py --check  # 只检查是否一致（CI 可用，不一致退 1）
"""
import filecmp
import shutil
import sys
from pathlib import Path

COMMON = [
    "winutil.py", "pngio.py", "win.py", "grab.py", "crop.py",
    "click.py", "key.py", "type.py", "paste.py", "diff.py",
]

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "skills" / "微信发消息" / "scripts"
DST = ROOT / "skills" / "预约自动入会" / "scripts"


def main():
    check_only = "--check" in sys.argv
    missing = [f for f in COMMON if not (SRC / f).exists()]
    if missing:
        print("源目录缺文件：", ", ".join(missing))
        return 2

    dirty = []
    for name in COMMON:
        a, b = SRC / name, DST / name
        same = b.exists() and filecmp.cmp(a, b, shallow=False)
        if same:
            continue
        dirty.append(name)
        if not check_only:
            shutil.copyfile(a, b)

    if not dirty:
        print("公共脚本已一致（%d 个文件）" % len(COMMON))
        return 0

    if check_only:
        print("不一致：", ", ".join(dirty))
        print("跑 python tools/sync_common.py 修复")
        return 1

    print("已同步：", ", ".join(dirty))
    return 0


if __name__ == "__main__":
    sys.exit(main())
