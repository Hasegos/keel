---
name: init
description: 현재 폴더에 keelkit 설정(CLAUDE.md, .claude/, docs/)을 설치한다. 기존 파일은 지우지 않고 읽어서 합치고, 프로젝트 내용을 채운다. 새 프로젝트를 시작하거나 기존 프로젝트에 keelkit을 붙일 때 쓴다.
disable-model-invocation: true
---

# keelkit 설치

현재 폴더(프로젝트 루트)에 keelkit을 설치하고, 기존 파일과 합치고, 프로젝트에 맞게 채운다. 기존 내용은 삭제하거나 요약하지 않는다.

## 1. 확인

현재 폴더가 프로젝트 루트인지 본다. 홈 폴더나 `~/.claude`이면 사용자에게 알리고 멈춘다.

## 2. 미리보기와 설치

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/install.py" --dry-run
python "${CLAUDE_PLUGIN_ROOT}/scripts/install.py"
```

`python`이 없으면 `python3`을 쓴다. 미리보기 결과를 표로 요약해서 사용자에게 보여주고 이어서 설치한다. 스크립트는 없는 파일만 만들고 `.claude/settings.json`은 권한과 hook을 JSON으로 더한다. 나머지 기존 파일은 건드리지 않고 백업만 남긴다.

## 3. 직접 합치기

결과에 "직접 합쳐야 함"이 있으면, 파일마다 `.keel-backup/<시각>/original/<경로>`(기존)와 `incoming/<경로>`(keelkit)를 읽고 프로젝트의 실제 파일에 합친다.

| 대상 | 합치는 방법 |
|---|---|
| `CLAUDE.md` | 기존 본문을 그대로 두고 keelkit의 0번 절, `Claude 설정`, `문서` 표를 추가한다. 같은 내용이 있으면 한 곳에만 둔다 |
| `docs/*.md` | 기존 내용을 유지하고, keelkit 뼈대에 있고 기존에 없는 절만 `미정`으로 추가한다 |
| `.claude/rules/*.md` | 기존 규칙을 유지한다. 서로 어긋나는 규칙은 어느 쪽을 쓸지 사용자에게 묻는다 |
| `.claude/hooks/*.py` | 기존 검사를 유지하고 keelkit의 검사를 추가한다. 합친 뒤 `python -m py_compile <파일>`로 문법을 확인한다 |
| skill, agent | 기존 것을 유지한다. 같은 이름이면 keelkit의 내용 중 없는 부분만 합친다 |

합칠 수 없는 항목은 그대로 두고 보고한다.

## 4. 채우기

프로젝트의 `.claude/skills/harness/SKILL.md`를 읽고 1번 절차를 그대로 따른다. 기존 `README`, `AGENTS.md`, 문서, 의존성 파일에서 읽을 수 있는 것은 먼저 읽어서 `{{변수}}`와 `미정`을 채우고, 못 읽는 것만 사용자에게 한 번에 묻는다.

## 5. 마무리

- 남은 `{{`와 `미정` 위치를 목록으로 알린다.
- 백업 폴더 `.keel-backup/`은 합친 결과를 확인한 뒤 사용자가 지운다 (삭제는 확인을 받는다).
- hook과 권한은 새 세션부터 적용된다고 알린다.
- `.claude/`, `docs/`, `CLAUDE.md`를 git에 올릴지는 사용자가 정한다.