# Quick Start Guide

Get FDE Life running locally in 5 minutes.

## Prerequisites

- Node.js 18+
- Go 1.21+
- Python 3.10+ with [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- xAI API key (get one at https://x.ai)

## Setup

### 1. Clone and Navigate

```bash
cd fde-life
```

### 2. Configure Agent

```bash
cd agent

# Create virtual environment and install dependencies
uv sync

# Set up environment
echo "XAI_API_KEY=your-api-key-here" > .env
```

### 3. Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

### 4. Install Backend Dependencies

```bash
cd ../backend
go mod download
```

## Running

Open three terminal windows:

### Terminal 1: Agent (Python gRPC Server)

```bash
cd agent
uv run python server.py
```

You should see: `Starting server on [::]:50051`

### Terminal 2: Backend (Go HTTP Server)

```bash
cd backend
go run main.go
```

You should see: `Starting server on :8080`

### Terminal 3: Frontend (Vite Dev Server)

```bash
cd frontend
npm run dev
```

You should see: `Local: http://localhost:3000/`

## Usage

1. Open http://localhost:3000 in your browser
2. Type a message and press Send
3. Watch the AI response stream in real-time

## Troubleshooting

### "Failed to call agent" error
- Ensure the Python agent is running on port 50051
- Check that `AGENT_ADDR` environment variable is correct (default: `localhost:50051`)

### Blank response or API errors
- Verify your xAI API key in `agent/.env`
- Check the agent terminal for error messages

### Frontend not loading
- Ensure `npm install` completed successfully
- Check that port 3000 is not in use

### CORS errors
- The backend includes CORS headers for `*`
- If issues persist, check the browser console for specific errors

## Ports Summary

| Service | Port | Protocol |
|---------|------|----------|
| Frontend | 3000 | HTTP |
| Backend | 8080 | HTTP |
| Agent | 50051 | gRPC |

## Next Steps

- Read the full [README.md](README.md) for architecture details
- Explore the API documentation in `openapi/openapi.yaml`
- Run tests with the commands in the README
