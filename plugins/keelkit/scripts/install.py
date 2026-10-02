import argparse
import copy
import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT   = Path(__file__).resolve().parent.parent
TEMPLATE      = PLUGIN_ROOT / "template"
BACKUP_ROOT   = ".keel-backup"
SETTINGS_REL  = ".claude/settings.json"
IGNORE_LINES  = (".env", ".keel-backup/")


def target_path(rel: Path) -> Path:
    """템플릿 안 경로를 프로젝트 안 경로로 바꾼다. claude/ 는 .claude/, CLAUDE.md.tpl 은 CLAUDE.md 가 된다.

    Args:
        rel: 템플릿 기준 상대 경로
    Returns:
        프로젝트 기준 상대 경로
    """
    parts = list(rel.parts)
    if parts[0] == "claude":
        parts[0] = ".claude"
    if parts[-1] == "CLAUDE.md.tpl":
        parts[-1] = "CLAUDE.md"
    return Path(*parts)


def github_repo(target: Path) -> str | None:
    """origin 원격이 GitHub 이면 owner/repo 를 반환한다.

    Args:
        target: 프로젝트 폴더
    Returns:
        owner/repo. 알 수 없으면 None
    """
    try:
        url = subprocess.run(["git", "-C", str(target), "remote", "get-url", "origin"], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"github\.com[:/]([^/\s]+/[^/\s]+?)(?:\.git)?$", url)
    return match.group(1) if match else None


def project_variables(target: Path) -> dict[str, str]:
    """스크립트가 확실히 알 수 있는 변수만 채운다. 나머지는 Claude 가 채운다.

    Args:
        target: 프로젝트 폴더
    Returns:
        변수 이름과 값
    """
    values = {"name": target.name, "today": datetime.date.today().isoformat()}
    repo = github_repo(target)
    if repo:
        values["repo"] = repo
    return values


def is_skipped(rel: str, skip: list[str]) -> bool:
    """건너뛸 경로인지 판단한다. 폴더를 주면 그 아래 전체가 해당한다.

    Args:
        rel: 프로젝트 기준 상대 경로
        skip: 건너뛸 경로 목록
    Returns:
        건너뛸 경로이면 True
    """
    return any(rel == s or rel.startswith(s + "/") for s in skip)


def drop_skipped_hooks(text: str, skip: list[str]) -> str:
    """건너뛴 hook 파일을 부르는 항목을 settings.json 본문에서 뺀다. 없는 파일을 가리키는 hook 이 남지 않게 한다.

    Args:
        text: settings.json 본문
        skip: 건너뛸 경로 목록
    Returns:
        hook 항목을 뺀 본문
    """
    data = json.loads(text)
    for event, groups in list(data.get("hooks", {}).items()):
        for group in groups:
            group["hooks"] = [h for h in group.get("hooks", []) if not any(s in h.get("command", "") for s in skip)]
        data["hooks"][event] = [g for g in groups if g["hooks"]]
    data["hooks"] = {event: groups for event, groups in data.get("hooks", {}).items() if groups}
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def render(rel: Path, variables: dict[str, str], skip: list[str]) -> str:
    """템플릿 파일을 읽어 변수를 채운다. 시스템에 python 이 없고 python3 만 있으면 hook 명령을 python3 으로 바꾼다.

    Args:
        rel: 템플릿 기준 상대 경로
        variables: 변수 이름과 값
        skip: 건너뛸 경로 목록. settings.json 에서 그 hook 을 뺀다
    Returns:
        변수를 채운 본문
    """
    text = (TEMPLATE / rel).read_text(encoding="utf-8")
    for key, value in variables.items():
        text = text.replace("{{" + key + "}}", value)
    if target_path(rel).as_posix() == SETTINGS_REL:
        if not shutil.which("python") and shutil.which("python3"):
            text = text.replace('"command": "python ', '"command": "python3 ')
        if skip:
            text = drop_skipped_hooks(text, skip)
    return text


def merge_settings(existing: dict, incoming: dict) -> dict:
    """기존 settings.json 에 keelkit 의 권한과 hook 을 더한다. 기존 항목은 지우지 않는다.

    Args:
        existing: 프로젝트의 기존 설정
        incoming: keelkit 설정
    Returns:
        합친 설정
    """
    merged = copy.deepcopy(existing)
    allow  = merged.setdefault("permissions", {}).setdefault("allow", [])
    for item in incoming.get("permissions", {}).get("allow", []):
        if item not in allow:
            allow.append(item)
    for event, groups in incoming.get("hooks", {}).items():
        have  = merged.setdefault("hooks", {}).setdefault(event, [])
        known = {h.get("command") for group in have for h in group.get("hooks", [])}
        for group in groups:
            fresh = [h for h in group.get("hooks", []) if h.get("command") not in known]
            if fresh:
                have.append({**group, "hooks": fresh})
    return merged


def plan(target: Path, variables: dict[str, str], skip: list[str]) -> list[dict]:
    """템플릿의 모든 파일을 프로젝트와 비교해서 처리 방식을 정한다.

    Args:
        target: 프로젝트 폴더
        variables: 변수 이름과 값
        skip: 건너뛸 경로 목록 (기존 것을 유지할 때)
    Returns:
        파일별 {rel, status, text}. status 는 new, same, merge, conflict, skip 중 하나
    """
    entries = []
    for source in sorted(TEMPLATE.rglob("*")):
        if not source.is_file() or "__pycache__" in source.parts:
            continue
        rel      = source.relative_to(TEMPLATE)
        dest_rel = target_path(rel)
        dest     = target / dest_rel
        if is_skipped(dest_rel.as_posix(), skip):
            entries.append({"rel": dest_rel.as_posix(), "text": "", "status": "skip"})
            continue
        text     = render(rel, variables, skip)
        entry    = {"rel": dest_rel.as_posix(), "text": text, "status": "new"}
        if dest.exists():
            try:
                current = dest.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                entry["status"] = "conflict"
                entries.append(entry)
                continue
            if current.replace("\r\n", "\n") == text.replace("\r\n", "\n"):
                entry["status"] = "same"
            elif entry["rel"] == SETTINGS_REL:
                entry.update(settings_status(current, text))
            else:
                entry["status"] = "conflict"
        entries.append(entry)
    return entries


def settings_status(current: str, incoming: str) -> dict:
    """settings.json 을 JSON 으로 합칠 수 있는지 판단한다.

    Args:
        current: 프로젝트의 기존 본문
        incoming: keelkit 본문
    Returns:
        status 와, 합칠 수 있으면 합친 본문(text)
    """
    try:
        existing = json.loads(current)
        merged   = merge_settings(existing, json.loads(incoming))
    except (ValueError, AttributeError, TypeError):
        return {"status": "conflict"}
    if merged == existing:
        return {"status": "same"}
    return {"status": "merge", "text": json.dumps(merged, ensure_ascii=False, indent=2) + "\n"}


def write_text(path: Path, text: str) -> None:
    """줄바꿈을 바꾸지 않고 UTF-8 로 쓴다.

    Args:
        path: 쓸 파일
        text: 본문
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def apply(entries: list[dict], target: Path, backup: Path) -> None:
    """계획대로 파일을 만든다. 합치거나 충돌하는 파일은 먼저 백업한다. 기존 파일은 지우지 않는다.

    Args:
        entries: plan 결과
        target: 프로젝트 폴더
        backup: 이번 실행의 백업 폴더
    """
    for entry in entries:
        dest = target / entry["rel"]
        if entry["status"] in ("merge", "conflict"):
            saved = backup / "original" / entry["rel"]
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dest, saved)
        if entry["status"] == "conflict":
            write_text(backup / "incoming" / entry["rel"], entry["text"])
        elif entry["status"] in ("new", "merge"):
            write_text(dest, entry["text"])


def ensure_gitignore(target: Path, dry_run: bool) -> list[str]:
    """git 저장소의 .gitignore 에 .env 와 백업 폴더를 넣는다.

    Args:
        target: 프로젝트 폴더
        dry_run: True 이면 쓰지 않고 추가할 줄만 계산한다
    Returns:
        추가한(추가할) 줄. git 저장소가 아니면 빈 목록
    """
    path = target / ".gitignore"
    if not path.exists() and not (target / ".git").exists():
        return []
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    lines   = {line.strip() for line in current.splitlines()}
    missing = [line for line in IGNORE_LINES if line not in lines]
    if missing and not dry_run:
        prefix = "" if not current or current.endswith("\n") else "\n"
        write_text(path, current + prefix + "\n".join(missing) + "\n")
    return missing


def report(entries: list[dict], ignored: list[str], target: Path, backup: Path, dry_run: bool) -> None:
    """처리 결과를 출력한다.

    Args:
        entries: plan 결과
        target: 프로젝트 폴더
        ignored: .gitignore 에 추가한(추가할) 줄
        backup: 이번 실행의 백업 폴더
        dry_run: 미리보기 여부
    """
    labels = [("new", "새로 만듦"), ("same", "이미 같음"), ("merge", "자동으로 합침"), ("conflict", "직접 합쳐야 함"), ("skip", "건너뜀 (기존 유지)")]
    print(f"keelkit 설치 {'미리보기' if dry_run else '결과'}: {target}")
    for status, label in labels:
        names = [e["rel"] for e in entries if e["status"] == status]
        if names:
            print(f"\n[{label}] {len(names)}개")
            for name in names:
                print(f"  - {name}")
    if any(e["status"] in ("merge", "conflict") for e in entries):
        print(f"\n백업: {backup.relative_to(target).as_posix()}/original (기존 파일), {backup.relative_to(target).as_posix()}/incoming (keelkit 파일)")
    if ignored:
        print(f"\n.gitignore {'에 추가할 줄' if dry_run else '에 추가함'}: {', '.join(ignored)}")


def main() -> int:
    """프로젝트 폴더에 keelkit 템플릿을 설치한다. 기존 파일은 지우거나 덮어쓰지 않는다.

    Returns:
        종료 코드
    """
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default=".", help="설치할 프로젝트 폴더 (기본: 현재 폴더)")
    parser.add_argument("--dry-run", action="store_true", help="파일을 쓰지 않고 계획만 출력한다")
    parser.add_argument("--skip", nargs="*", default=[], help="설치하지 않을 경로 (프로젝트 기준, 폴더 가능). 기존 것을 유지할 때 쓴다")
    args   = parser.parse_args()
    target = Path(args.target).resolve()
    skip   = [s for s in (p.replace("\\", "/").strip("/") for p in args.skip) if s]

    if not target.is_dir() or target == Path.home() or (target / ".claude-plugin").exists():
        print(f"설치할 수 없는 폴더입니다: {target}", file=sys.stderr)
        return 1

    entries = plan(target, project_variables(target), skip)
    stamp   = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup  = target / BACKUP_ROOT / stamp
    if not args.dry_run:
        apply(entries, target, backup)
    ignored = ensure_gitignore(target, args.dry_run)
    report(entries, ignored, target, backup, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())