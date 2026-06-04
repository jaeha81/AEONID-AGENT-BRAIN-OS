# Work Order

이 파일은 버키에이전트가 Codex 또는 Claude Code에게 내리는 현재 작업 지시서이다.

## Current Assignment

- Status: ready
- Project: AEONID-AGENT-BRAIN-OS
- Branch: `laptop/main-dev`
- Worker role: laptop branch developer
- Primary app folder: `frontend`

## Startup Instruction

작업자는 새 세션을 시작하면 아래 순서로 진행한다.

1. `AGENTS.md` 또는 `CLAUDE.md`를 읽는다.
2. `docs/agent-system/BUCKY_STARTUP.md`를 읽는다.
3. `docs/agent-system/BRANCH_ROLE_LAPTOP.md`를 읽는다.
4. 이 `WORK_ORDER.md`를 읽는다.
5. `git status --short --branch`로 현재 상태를 확인한다.
6. 작업 목적, 수정 대상, 검증 방법을 먼저 보고한다.
7. 사용자 승인 또는 명확한 요청이 있으면 개발에 착수한다.

## Default Development Target

현재 기본 개발 대상은 프론트엔드이다.

```text
frontend
```

기본 검증 명령:

```powershell
cd frontend
npm.cmd run build
```

## Next Work Slot

아직 특정 기능 개발 지시는 없다.

다음 개발 요청이 들어오면 이 파일의 `Next Work Slot`을 갱신하거나, 작업 요청 내용을 기준으로 바로 착수한다.

## Handoff Rule

작업 완료 후 집PC에서 이어받을 수 있도록 다음 명령을 안내한다.

```powershell
cd C:\ai프로젝트\AEONID-AGENT-BRAIN-OS
git fetch origin
git switch laptop/main-dev
git pull
```

