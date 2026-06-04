# Branch Role: Laptop PC

이 프로젝트에서 현재 PC는 노트북 개발 PC 역할이다.

## Branch

```text
laptop/main-dev
```

## Local Folder

권장 로컬 경로:

```text
C:\JH-DEV\AEONID-laptop
```

현재 세션의 실제 경로가 다르더라도, 열린 프로젝트 루트를 기준으로 작업한다.

## Role

노트북 PC는 이동 중 개발, 기능 초안 작성, UI 보완, 문서 정리, Codex/Claude Code 작업 검증을 담당한다.

## Do

- `laptop/main-dev`에서 작업한다.
- 작업 전 `git pull`로 최신 상태를 받는다.
- 작업 후 `git push`로 GitHub에 올린다.
- 집PC에서 이어받을 수 있게 커밋 메시지를 명확하게 작성한다.
- 프론트엔드 명령은 `frontend` 폴더에서 실행한다.

## Do Not

- `main`에 직접 커밋하지 않는다.
- `.env.local`을 커밋하지 않는다.
- GitHub에 API key, token, password를 올리지 않는다.
- 검증 없이 대규모 구조 변경을 하지 않는다.
- 루트에서 `npm install`을 실행하지 않는다. 이 프로젝트의 `package.json`은 `frontend` 안에 있다.

## Standard Commands

작업 시작:

```powershell
cd C:\JH-DEV\AEONID-laptop
git status --short --branch
git pull
```

프론트엔드 실행:

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

작업 종료:

```powershell
cd C:\JH-DEV\AEONID-laptop
git status
git add .
git commit -m "Update laptop branch work"
git push
```

