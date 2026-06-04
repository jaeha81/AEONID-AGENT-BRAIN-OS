# JH Claude Code Laptop Branch Rule

이 프로젝트는 Claude Code가 `laptop/main-dev` 브랜치에서 개발을 이어가기 위한 작업 폴더이다.

## Required Startup Read

Claude Code는 작업 시작 전 반드시 다음 파일을 읽는다.

1. `docs/agent-system/BUCKY_STARTUP.md`
2. `docs/agent-system/BRANCH_ROLE_LAPTOP.md`
3. `docs/agent-system/WORK_ORDER.md`

## Branch Policy

- 현재 PC 역할: 노트북 개발 PC
- 작업 브랜치: `laptop/main-dev`
- `main` 브랜치 직접 수정 금지
- 작업 완료 후 `git push`로 GitHub에 올려 집PC에서 이어받게 한다.

## Project Commands

프론트엔드 실행 위치:

```text
frontend
```

개발 실행:

```powershell
cd C:\JH-DEV\AEONID-laptop\frontend
npm.cmd install
npm.cmd run dev
```

빌드 검증:

```powershell
cd C:\JH-DEV\AEONID-laptop\frontend
npm.cmd run build
```

## Completion Rule

수정 후에는 다음을 보고한다.

- 변경 파일
- 변경 요약
- 실행/빌드 결과
- 커밋/푸쉬 필요 여부
- 집PC에서 이어받는 방법

