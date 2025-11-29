package api

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"fde-life/pb"

	"google.golang.org/grpc"
)

// MockChatServiceClient
type MockChatServiceClient struct {
	StreamChatFunc func(ctx context.Context, in *pb.ChatRequest, opts ...grpc.CallOption) (pb.ChatService_StreamChatClient, error)
}

func (m *MockChatServiceClient) StreamChat(ctx context.Context, in *pb.ChatRequest, opts ...grpc.CallOption) (pb.ChatService_StreamChatClient, error) {
	return m.StreamChatFunc(ctx, in, opts...)
}

// MockStream
type MockStream struct {
	grpc.ClientStream
	RecvFunc func() (*pb.ChatResponse, error)
}

func (m *MockStream) Recv() (*pb.ChatResponse, error) {
	return m.RecvFunc()
}

func TestHandleChat(t *testing.T) {
	// Setup Mock
	mockStream := &MockStream{
		RecvFunc: func() (*pb.ChatResponse, error) {
			return nil, io.EOF
		},
	}

	// We need to simulate a sequence of responses
	responses := []*pb.ChatResponse{
		{Chunk: "Hello"},
		{Chunk: " World"},
	}
	responseIdx := 0

	mockStream.RecvFunc = func() (*pb.ChatResponse, error) {
		if responseIdx >= len(responses) {
			return nil, io.EOF
		}
		resp := responses[responseIdx]
		responseIdx++
		return resp, nil
	}

	mockClient := &MockChatServiceClient{
		StreamChatFunc: func(ctx context.Context, in *pb.ChatRequest, opts ...grpc.CallOption) (pb.ChatService_StreamChatClient, error) {
			return mockStream, nil
		},
	}

	// Setup Handler
	handler := &ChatHandler{
		grpcClient: mockClient,
	}

	// Create Request
	reqBody := ChatRequest{
		Messages: []Message{{Role: "user", Content: "Hi"}},
	}
	body, _ := json.Marshal(reqBody)
	req := httptest.NewRequest("POST", "/api/chat", bytes.NewReader(body))
	w := httptest.NewRecorder()

	// Execute
	handler.HandleChat(w, req)

	// Verify
	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	// Check body
	bodyBytes, _ := io.ReadAll(resp.Body)
	expected := "data: Hello\n\ndata:  World\n\n"
	if string(bodyBytes) != expected {
		t.Errorf("Expected body %q, got %q", expected, string(bodyBytes))
	}
}
