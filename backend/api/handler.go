package api

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"fde-life/pb"

	"github.com/go-chi/chi/v5"
	"google.golang.org/grpc"
)

type ChatHandler struct {
	grpcClient pb.ChatServiceClient
}

func NewChatHandler(conn *grpc.ClientConn) *ChatHandler {
	return &ChatHandler{
		grpcClient: pb.NewChatServiceClient(conn),
	}
}

func (h *ChatHandler) RegisterRoutes(r chi.Router) {
	r.Post("/api/chat", h.HandleChat)
}

type ChatRequest struct {
	Messages []Message `json:"messages"`
}

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

func (h *ChatHandler) HandleChat(w http.ResponseWriter, r *http.Request) {
	var req ChatRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Convert to gRPC request
	grpcReq := &pb.ChatRequest{
		Messages: make([]*pb.Message, len(req.Messages)),
	}
	for i, msg := range req.Messages {
		grpcReq.Messages[i] = &pb.Message{
			Role:    msg.Role,
			Content: msg.Content,
		}
	}

	// Call gRPC stream
	stream, err := h.grpcClient.StreamChat(context.Background(), grpcReq)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to call agent: %v", err), http.StatusInternalServerError)
		return
	}

	// Set headers for SSE
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming not supported", http.StatusInternalServerError)
		return
	}

	for {
		resp, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			// Log error and maybe send an error event?
			// For now just stop.
			fmt.Printf("Stream error: %v\n", err)
			break
		}

		// Send chunk
		// We can send just the text or a JSON object.
		// Let's send the raw chunk for simplicity, or a JSON structure.
		// The client expects a stream.
		// Let's send: data: <content>\n\n
		
		// If there is thinking, we might want to send that too.
		// For now, just the chunk.
		
		if resp.Chunk != "" {
			fmt.Fprintf(w, "data: %s\n\n", resp.Chunk)
			flusher.Flush()
		}
	}
}
