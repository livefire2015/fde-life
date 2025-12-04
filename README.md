# FDE Life

An AI chat application powered by xAI's Grok-4-fast model with real-time streaming responses.

## Architecture

```
┌─────────────┐     HTTP/SSE      ┌─────────────┐      gRPC       ┌─────────────┐
│   Frontend  │ ───────────────▶  │   Backend   │ ──────────────▶ │    Agent    │
│  (SolidJS)  │ ◀───────────────  │    (Go)     │ ◀────────────── │  (Python)   │
│  Port 3000  │                   │  Port 8080  │                 │  Port 50051 │
└─────────────┘                   └─────────────┘                 └─────────────┘
                                                                         │
                                                                         ▼
                                                                   ┌───────────┐
                                                                   │  xAI API  │
                                                                   │ (Grok-4)  │
                                                                   └───────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | SolidJS, Vite, TailwindCSS | Chat UI with real-time streaming |
| **Backend** | Go, Chi router | HTTP-to-gRPC bridge, SSE streaming |
| **Agent** | Python, gRPC, xAI SDK | AI model integration with tools |

### Features

- Real-time streaming responses via Server-Sent Events
- Message history for contextual conversations
- Tool support: web search, X search, code execution
- Dark mode UI with responsive design

## Project Structure

```
fde-life/
├── frontend/          # SolidJS web application
│   └── src/
│       └── App.tsx    # Main chat component
├── backend/           # Go HTTP server
│   ├── api/           # HTTP handlers
│   ├── pb/            # Generated protobuf code
│   └── main.go        # Entry point
├── agent/             # Python gRPC server
│   ├── generated/     # Generated protobuf code
│   ├── tests/         # Unit tests
│   └── server.py      # gRPC service implementation
├── proto/             # Protocol buffer definitions
│   └── chat.proto     # ChatService definition
└── openapi/           # OpenAPI specifications
```

## Requirements

- Node.js 18+
- Go 1.21+
- Python 3.10+ with [uv](https://docs.astral.sh/uv/)
- xAI API key

## Quick Start

See [QUICK_START.md](QUICK_START.md) for setup instructions.

## Development

### Running Tests

```bash
# Frontend
cd frontend && npm test

# Backend
cd backend && go test ./... -v

# Agent
cd agent && uv run pytest tests/ -v
```

### Protocol Buffers

The gRPC interface is defined in `proto/chat.proto`. After making changes, regenerate:

```bash
# Python (from agent/)
uv run python -m grpc_tools.protoc -I../proto --python_out=./generated --grpc_python_out=./generated ../proto/chat.proto

# Go (from backend/)
protoc --go_out=./pb --go-grpc_out=./pb -I../proto ../proto/chat.proto
```

## API

### POST /api/chat

Send a chat message and receive streaming response.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ]
}
```

**Response:** Server-Sent Events stream
```
data: Hello
data: ! I'm
data:  doing great
data: , thanks for asking!
```

## License

Private - All rights reserved
