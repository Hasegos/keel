# keelkit

> 어떤 프로젝트든 같은 뼈대로 시작한다. 폴더를 열고 `/keelkit:init` 한 줄이면 `CLAUDE.md`, `.claude/`, `docs/`가 깔리고 Claude가 프로젝트를 읽어서 채운다.

Claude Code 플러그인. 특정 언어나 프레임워크에 묶이지 않는다.

## 설치

```bash
/plugin marketplace add Hasegos/keelkit
/plugin install keelkit@keelkit
```

프로젝트 폴더를 새 세션으로 열고 실행한다.

```bash
/keelkit:init
```

hook과 권한은 새 세션부터 적용된다.

## 무엇이 깔리나

```
my-project/
├─ CLAUDE.md                 소개, 명령, 설정 지도 (매번 읽힘)
├─ docs/
│  ├─ ROADMAP.md             목적, 진행 상황, 결정 기록
│  ├─ ARCHITECTURE.md        구조와 설계 근거
│  └─ SETUP.md               실행법, .env 키 이름
└─ .claude/
   ├─ settings.json          권한 + hook 연결
   ├─ rules/                 진행 방식, 코드, 주석, 문서 규칙
   ├─ skills/                harness(설정 채우기 · 변경), verify, commit-pr
   ├─ agents/                runner(긴 출력 요약), reviewer(큰 PR 검토)
   └─ hooks/                 guard.py, strip_eof.py
```

설치 뒤 Claude가 코드와 기존 문서를 읽고 목적, 스택, 실행 명령을 채운다. 읽어서 알 수 없는 것만 한 번에 묻는다.

## 기존 프로젝트에 붙일 때

기존 파일은 지우거나 덮어쓰지 않는다. 파일 이름이 아니라 **기능** 단위로 겹침을 먼저 확인하고, 설치 전에 한 번만 묻는다.

1. Claude가 기존 `CLAUDE.md`, `.claude/`, hook, `.husky` 등을 읽고 keelkit의 기능 15개와 대조한다.
2. 기능마다 번호를 붙인 표로 보여준다: 겹침 · 내용 다름, 겹침 · 내용 같음, 없음.
3. 기본값은 **기존 유지**다. 바꿀 번호만 말하면 된다 (예: "1번, 3번 keelkit으로". 없으면 "그대로").
4. 겹치지 않는 기능만 설치한다. 기존을 지우는 선택은 한 번 더 확인하고 백업을 남긴다.

| 상황 | 처리 |
|---|---|
| 같은 기능이 없음 | keelkit을 설치한다 |
| 같은 기능이 있음 | 기존을 유지하고 keelkit 쪽은 설치하지 않는다 |
| `.claude/settings.json` | 기존 권한과 hook은 유지하고 keelkit 것만 추가한다 |
| `guard.py`의 검사 중 일부가 겹침 | 그 검사만 끈다. 기존 hook 코드는 건드리지 않는다 |

- `.gitignore`에는 `.env`와 `.keel-backup/`만 추가한다.
- 합친 결과를 확인한 뒤 `.keel-backup/`은 직접 지운다.

## guard hook이 막는 것

부탁이 아니라 동작으로 막는다.

| 상황 | 동작 |
|---|---|
| `master` / `main`에 merge, push, PR 병합 | 차단 |
| 커밋 메시지에 `Co-Authored-By` | 차단 |
| `.env` 커밋, `.env.*` 파일 생성 | 차단 |
| 파일, 폴더, 브랜치, 태그, 컨테이너 삭제, 강제 push | 사용자에게 확인 요청 |
| `feature/` 브랜치 삭제 | 자동 허용 |

## 기본 진행 규칙

- 프로젝트 안 작업(수정, 실행, 브랜치, 커밋, push, PR)은 묻지 않고 진행한다.
- 기준 브랜치는 `dev`, 작업 브랜치는 `feature/<짧은이름>-<기능>`.
- 커밋은 `ADD` / `FIX` / `DELETE <대상> 추가/수정/삭제`.
- PR은 `gh`로 만들고 squash 병합한다. `master` / `main` 병합은 사용자가 직접 한다.
- `.env`는 한 개만 쓴다. 키 이름만 `docs/SETUP.md`에 적고 값은 적지 않는다.
- 주석은 클래스 · 함수 단위에만, 언어 표준 문서 주석(Javadoc, docstring, JSDoc 등)으로 쓴다.

기본값을 바꾸려면 Claude에게 "이 규칙 바꿔줘"라고 말한다. `harness` skill이 알맞은 파일을 찾아서 고친다.

## 요구 사항

- Claude Code
- Python 3 (`python` 또는 `python3`)
- git
- 선택: `gh` (PR 생성 · 병합). 없으면 설치와 `gh auth login`을 안내하고 PR 단계는 보류한다.

## 자주 묻는 것

| 질문 | 답 |
|---|---|
| 일부만 쓸 수 있나? | 설치 뒤 필요 없는 파일을 지우면 된다. |
| 플러그인을 업데이트하면? | `/keelkit:init`을 다시 실행한다. 이미 채운 파일은 덮어쓰지 않고 "직접 합쳐야 함"으로만 보고하며 백업이 남는다. |
| hook이 동작하지 않는다 | 새 세션에서 열었는지, `python`이 PATH에 있는지 확인한다. |

## 라이선스

MIT
