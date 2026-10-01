# keel

> 어떤 프로젝트든 같은 뼈대로 시작한다. 폴더를 열고 `/keel:init` 한 줄이면 `CLAUDE.md`, `.claude/`, `docs/`가 깔리고 Claude가 프로젝트를 읽어서 채운다.

Claude Code 플러그인. 특정 언어나 프레임워크에 묶이지 않는다.

## 설치

```bash
/plugin marketplace add Hasegos/keel
/plugin install keel@keel
```

프로젝트 폴더를 새 세션으로 열고 실행한다.

```bash
/keel:init
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

기존 파일은 지우거나 덮어쓰지 않는다.

| 파일 | 처리 |
|---|---|
| 없음 | 새로 만든다 |
| 내용이 같음 | 건너뛴다 |
| `.claude/settings.json` | 기존 권한과 hook은 유지하고 keel 것만 추가한다 |
| 그 외 (`CLAUDE.md`, `docs/*`, `rules/*` 등) | `.keel-backup/<시각>/`에 기존 파일과 keel 파일을 복사해 두고, Claude가 둘을 읽어서 합친다. 규칙이 서로 어긋나면 어느 쪽을 쓸지 묻는다 |

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
| 플러그인을 업데이트하면? | `/keel:init`을 다시 실행한다. 이미 채운 파일은 덮어쓰지 않고 "직접 합쳐야 함"으로만 보고하며 백업이 남는다. |
| hook이 동작하지 않는다 | 새 세션에서 열었는지, `python`이 PATH에 있는지 확인한다. |

## 라이선스

MIT
