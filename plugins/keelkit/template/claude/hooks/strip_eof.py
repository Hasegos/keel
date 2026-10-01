import json
import os
import sys
from pathlib import Path

SKIP_PARTS = {"node_modules", ".git", "dist", "__pycache__"}
SKIP_NAMES = {"package.json", "package-lock.json"}
SKIP_DIRS  = ()


def main() -> None:
    """수정한 파일 끝의 빈 줄을 지운다. 생성 도구가 만드는 파일(package*.json, node_modules 등)은 건드리지 않는다."""
    event = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    raw   = (event.get("tool_input") or {}).get("file_path")
    root  = os.environ.get("CLAUDE_PROJECT_DIR")
    if not raw or not root:
        return

    path = Path(raw).resolve()
    try:
        rel = path.relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return
    if SKIP_PARTS & set(path.parts) or path.name in SKIP_NAMES or rel.startswith(SKIP_DIRS) or not path.is_file():
        return

    data = path.read_bytes()
    if b"\0" in data[:1024]:
        return
    stripped = data.rstrip(b"\r\n")
    if stripped != data:
        path.write_bytes(stripped)


if __name__ == "__main__":
    main()