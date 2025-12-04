# Repository Guidelines

## Project Structure & Module Organization
`frontend/` holds the SolidJS chat UI (Vite + Tailwind) with entry points in `src/index.tsx` and UI tests beside components. `backend/` is a Go HTTP façade (`main.go`) that exposes `/api/chat` and proxies streaming replies to the browser via SSE, while request/response types live in `backend/api`. `agent/` contains the Python gRPC agent (`server.py`) plus generated stubs in `agent/generated` and unit tests in `agent/tests`. Contract files live in `proto/chat.proto`, the compiled Go stubs under `backend/pb`, and HTTP schema notes in `openapi/openapi.yaml`; docs and walkthroughs sit in `docs/`.

## Build, Test, and Development Commands
- `npm install --prefix frontend && npm run dev --prefix frontend` starts the Solid dev server, while `npm run build --prefix frontend` produces the static bundle consumed by any host.  
- `go run ./backend` boots the REST bridge (set `PORT` and `AGENT_ADDR` as needed); `go test ./...` from `backend/` exercises the handler and pb packages.  
- `uv run pytest agent/tests` runs the agent suite, and `uv run python agent/server.py` launches the async gRPC server locally.  
- Regenerate APIs whenever `proto/chat.proto` changes: `uv run python -m grpc_tools.protoc -I proto --python_out=agent/generated --grpc_python_out=agent/generated proto/chat.proto` and `protoc --go_out=backend/pb --go-grpc_out=backend/pb proto/chat.proto`.

## Coding Style & Naming Conventions
Lean on TypeScript + JSX in `frontend/src`; components and test files follow `PascalCase.tsx` / `*.test.tsx`, hooks and helpers stay camelCase, and Tailwind utility classes should remain declarative rather than embedded CSS. Go code must stay gofmt’ed, keep handlers in small files under `backend/api`, and prefer explicit context passing to globals. Python agent code follows PEP8 with 4‑space indents; keep gRPC/service definitions in `server.py` and pure helpers under `agent/` submodules when they grow.

## Testing Guidelines
Vitest (configured through `vitest.config.ts` and `src/setupTests.ts`) powers UI tests; colocate new suites next to their components and assert streamed rendering behavior. Go packages rely on the standard `testing` package—mock `pb.ChatServiceClient` like `handler_test.go` does and cover SSE edge cases. Python tests run through pytest but can use `unittest.IsolatedAsyncioTestCase` as shown in `agent/tests/test_server.py`; seed mocked `xai_sdk` clients and cover token streaming branches when changing inference logic.

## Commit & Pull Request Guidelines
Recent history follows Conventional Commits with optional scopes (`fix(frontend): …`, `docs: …`, `refactor(agent): …`), so keep that style for easy changelog generation. Each PR should describe the feature, outline backend/agent impacts, list manual or automated test runs, and link the relevant issue or spec. UI or API-facing changes also need before/after screenshots or example curl/Vite outputs alongside any new environment variable requirements.

## Configuration & Security
Both backend and agent read secrets such as xAI keys via `.env`; never commit that file and document required env vars in the PR body. When exposing new endpoints, update `openapi/openapi.yaml` plus `docs/VERIFICATION_WALKTHROUGH.md`, and note any firewall or auth implications so deployment agents can mirror them.
