# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FDE Life is an AI chat application with a three-tier architecture:
- **Frontend**: SolidJS + Vite + TailwindCSS (TypeScript)
- **Backend**: Go HTTP server (chi router) that proxies to the agent via gRPC
- **Agent**: Python gRPC server using xAI SDK (Grok-4-fast model)

Communication flow: Frontend -> HTTP/SSE -> Backend -> gRPC streaming -> Agent -> xAI API

## Development Commands

### Frontend (from `frontend/`)
```bash
npm run dev          # Start dev server on port 3000
npm run build        # Production build
npm test             # Run tests (vitest)
npm run test:watch   # Run tests in watch mode
```

### Backend (from `backend/`)
```bash
go run main.go       # Start server on port 8080 (or PORT env)
go test ./... -v     # Run all tests
```

### Agent (from `agent/`)
```bash
uv run python server.py             # Start gRPC server on port 50051
uv run pytest tests/ -v             # Run tests
```

## Architecture

### Data Flow
1. Frontend sends POST to `/api/chat` with message history
2. Backend receives HTTP request, converts to gRPC `ChatRequest`
3. Backend calls Agent's `StreamChat` RPC, receives streaming responses
4. Backend converts gRPC stream to SSE (`data: <chunk>\n\n`)
5. Frontend reads SSE stream and updates UI reactively

### Key Files
- `proto/chat.proto` - gRPC service definition (ChatService with StreamChat RPC)
- `backend/api/handler.go` - HTTP to gRPC bridge, SSE streaming
- `agent/server.py` - gRPC server with xAI SDK integration
- `frontend/src/App.tsx` - Main chat UI component

### Environment Variables
- `agent/.env` - Must contain xAI API key for the agent
- `PORT` - Backend HTTP port (default: 8080)
- `AGENT_ADDR` - Backend's gRPC target (default: localhost:50051)

## Code Generation

Protobuf files need regeneration if `proto/chat.proto` changes:
- Go: Generated to `backend/pb/`
- Python: Generated to `agent/generated/`

## Testing Notes

- Frontend tests use jsdom; full SolidJS component rendering has limitations in test environment
- Backend tests mock the gRPC client for isolation
- Agent tests use `SampleChat` (mock-based) rather than `StreamChat` (real xAI calls)
