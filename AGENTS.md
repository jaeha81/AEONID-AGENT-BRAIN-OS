# JH Codex Laptop Branch Rule

이 프로젝트는 노트북 PC 개발 브랜치 기준으로 운영한다.

## Fixed Role

- Project: AEONID-AGENT-BRAIN-OS
- Recommended local folder: `C:\JH-DEV\AEONID-laptop`
- Branch: `laptop/main-dev`
- Main branch policy: do not modify `main` directly.
- Central source: GitHub `origin`

## Startup Order

Codex는 작업 시작 전 반드시 아래 파일을 순서대로 읽는다.

1. `docs/agent-system/BUCKY_STARTUP.md`
2. `docs/agent-system/BRANCH_ROLE_LAPTOP.md`
3. `docs/agent-system/WORK_ORDER.md`

읽은 뒤 바로 수정하지 말고 먼저 다음 내용을 보고한다.

- 작업 목적
- 현재 브랜치
- 수정 대상 파일
- 실행/빌드 검증 방법
- 보안 또는 배포상 주의점

## Development Rules

- 모든 개발은 `laptop/main-dev`에서 진행한다.
- 작업 시작 전 `git status --short --branch`를 확인한다.
- 작업 시작 전 가능하면 `git pull`로 원격 브랜치를 최신화한다.
- 루트에는 `package.json`이 없으므로 프론트엔드 명령은 `frontend`에서 실행한다.
- PowerShell에서는 `npm` 대신 `npm.cmd` 사용을 우선한다.
- API key, token, password는 `.env.local` 또는 환경변수에 둔다.
- `.env.local`은 GitHub에 올리지 않는다.
- 불필요한 의존성을 추가하지 않는다.
- 기존 구조를 크게 바꾸지 않고 필요한 파일만 수정한다.

## Commands

작업 시작:

```powershell
cd C:\JH-DEV\AEONID-laptop
git status --short --branch
git pull
cd frontend
npm.cmd install
npm.cmd run dev
```

검증:

```powershell
cd C:\JH-DEV\AEONID-laptop\frontend
npm.cmd run build
```

작업 종료:

```powershell
cd C:\JH-DEV\AEONID-laptop
git status
git add .
git commit -m "Update laptop work"
git push
```

