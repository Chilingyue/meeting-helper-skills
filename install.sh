#!/usr/bin/env bash
# 把 skills/* 安装到本机 Agent 的技能目录（Git Bash / WSL / MSYS 下可用）。
#
# 用法：
#   ./install.sh                       # 默认 %USERPROFILE%/.workbuddy/skills
#   ./install.sh ~/.claude/skills      # 指定目标
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$ROOT/skills"
DEST="${1:-$HOME/.workbuddy/skills}"
STAMP="$(date +%Y%m%d-%H%M%S)"

[ -d "$SRC" ] || { echo "找不到 skills 目录：$SRC" >&2; exit 1; }
mkdir -p "$DEST"

for d in "$SRC"/*/; do
  name="$(basename "$d")"
  target="$DEST/$name"
  if [ -e "$target" ]; then
    mv "$target" "$target.bak-$STAMP"
    echo "已备份旧版本 -> $target.bak-$STAMP"
  fi
  cp -r "$d" "$target"
  echo "已安装 $name -> $target（$(find "$target" -type f | wc -l) 个文件）"
done

echo
echo "完成。重启 Agent 客户端后即可触发。"
echo "提示：脚本只用 Python 标准库；cvfind.py 额外需要 opencv-python-headless numpy。"
