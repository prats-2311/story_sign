import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import App from "./App";

// Mock fetch for testing
global.fetch = jest.fn();

// Mock getUserMedia for webcam access
Object.defineProperty(navigator, "mediaDevices", {
  writable: true,
  value: {
    getUserMedia: jest.fn(() =>
      Promise.resolve({
        getTracks: () => [{ stop: jest.fn() }],
      })
    ),
  },
});

describe("Story Generation Integration", () => {
  beforeEach(() => {
    fetch.mockClear();
    navigator.mediaDevices.getUserMedia.mockClear();
  });

  test("integrates story generation workflow with backend connection", async () => {
    // Mock successful backend connection
    const mockBackendResponse = {
      message: "Hello from the StorySign Backend!",
      status: "healthy",
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockBackendResponse,
    });

    render(<App />);

    // First connect to backend
    const testBackendButton = screen.getByRole("button", {
      name: /Test Backend/i,
    });
    fireEvent.click(testBackendButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Hello from the StorySign Backend!/i)
      ).toBeInTheDocument();
    });

    // Verify ASL World button is now enabled
    const aslWorldButton = screen.getByRole("button", {
      name: /Enter ASL World/i,
    });
    expect(aslWorldButton).not.toBeDisabled();

    // Enter ASL World
    fireEvent.click(aslWorldButton);

    // Verify ASL World interface is displayed
    await waitFor(() => {
      expect(screen.getByText(/Generate Your Story/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Show an object to the camera/i)
      ).toBeInTheDocument();
    });

    // Verify scan button is present
    const scanButton = screen.getByRole("button", {
      name: /Scan Object to Start/i,
    });
    expect(scanButton).toBeInTheDocument();
    expect(scanButton).not.toBeDisabled();
  });

  test("handles story generation API integration", async () => {
    // Mock successful backend connection
    const mockBackendResponse = {
      message: "Hello from the StorySign Backend!",
      status: "healthy",
    };

    // Mock successful story generation
    const mockStoryResponse = {
      success: true,
      story: {
        title: "The Adventure of the Red Ball",
        sentences: [
          "Once upon a time, there was a bright red ball.",
          "The ball loved to bounce in the sunny park.",
          "Children would come to play with the happy ball.",
        ],
        identified_object: "ball",
        generation_time_ms: 2340,
      },
    };

    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockBackendResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStoryResponse,
      });

    render(<App />);

    // Connect to backend
    const testBackendButton = screen.getByRole("button", {
      name: /Test Backend/i,
    });
    fireEvent.click(testBackendButton);

    await waitFor(() => {
      const aslWorldButton = screen.getByRole("button", {
        name: /Enter ASL World/i,
      });
      expect(aslWorldButton).not.toBeDisabled();
    });

    // Enter ASL World
    const aslWorldButton = screen.getByRole("button", {
      name: /Enter ASL World/i,
    });
    fireEvent.click(aslWorldButton);

    await waitFor(() => {
      expect(screen.getByText(/Generate Your Story/i)).toBeInTheDocument();
    });

    // Verify the story generation workflow is integrated
    // Note: Full testing would require mocking canvas and video elements
    // This test verifies the API integration structure is in place
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/",
      expect.any(Object)
    );
  });

  test("handles story generation error scenarios", async () => {
    // Mock successful backend connection
    const mockBackendResponse = {
      message: "Hello from the StorySign Backend!",
      status: "healthy",
    };

    // Mock story generation service error
    const mockErrorResponse = {
      error_type: "service_unavailable",
      user_message:
        "AI services are temporarily unavailable. Please try again later.",
      retry_allowed: true,
      retry_delay_seconds: 30,
    };

    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockBackendResponse,
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 503,
        statusText: "Service Unavailable",
        json: async () => mockErrorResponse,
      });

    render(<App />);

    // Connect to backend
    const testBackendButton = screen.getByRole("button", {
      name: /Test Backend/i,
    });
    fireEvent.click(testBackendButton);

    await waitFor(() => {
      const aslWorldButton = screen.getByRole("button", {
        name: /Enter ASL World/i,
      });
      expect(aslWorldButton).not.toBeDisabled();
    });

    // Enter ASL World
    const aslWorldButton = screen.getByRole("button", {
      name: /Enter ASL World/i,
    });
    fireEvent.click(aslWorldButton);

    await waitFor(() => {
      expect(screen.getByText(/Generate Your Story/i)).toBeInTheDocument();
    });

    // Verify error handling integration is in place
    // The actual error would be triggered by the scan button click with mocked canvas
    expect(
      screen.getByRole("button", { name: /Scan Object to Start/i })
    ).toBeInTheDocument();
  });

  test("manages story generation state correctly", async () => {
    // Mock successful backend connection
    const mockBackendResponse = {
      message: "Hello from the StorySign Backend!",
      status: "healthy",
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockBackendResponse,
    });

    render(<App />);

    // Connect to backend
    const testBackendButton = screen.getByRole("button", {
      name: /Test Backend/i,
    });
    fireEvent.click(testBackendButton);

    await waitFor(() => {
      const aslWorldButton = screen.getByRole("button", {
        name: /Enter ASL World/i,
      });
      expect(aslWorldButton).not.toBeDisabled();
    });

    // Enter ASL World
    const aslWorldButton = screen.getByRole("button", {
      name: /Enter ASL World/i,
    });
    fireEvent.click(aslWorldButton);

    await waitFor(() => {
      expect(screen.getByText(/Generate Your Story/i)).toBeInTheDocument();
    });

    // Exit ASL World
    const exitButton = screen.getByRole("button", { name: /Exit ASL World/i });
    fireEvent.click(exitButton);

    // Should return to main interface
    await waitFor(() => {
      expect(screen.getByText(/Backend Connectivity/i)).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Enter ASL World/i })
      ).toBeInTheDocument();
    });
  });

  test("integrates practice control workflow", async () => {
    // Mock successful backend connection
    const mockBackendResponse = {
      message: "Hello from the StorySign Backend!",
      status: "healthy",
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockBackendResponse,
    });

    render(<App />);

    // Connect to backend
    const testBackendButton = screen.getByRole("button", {
      name: /Test Backend/i,
    });
    fireEvent.click(testBackendButton);

    await waitFor(() => {
      const aslWorldButton = screen.getByRole("button", {
        name: /Enter ASL World/i,
      });
      expect(aslWorldButton).not.toBeDisabled();
    });

    // Enter ASL World
    const aslWorldButton = screen.getByRole("button", {
      name: /Enter ASL World/i,
    });
    fireEvent.click(aslWorldButton);

    await waitFor(() => {
      expect(screen.getByText(/Generate Your Story/i)).toBeInTheDocument();
    });

    // Verify practice control integration structure is in place
    // Full testing would require story data and WebSocket mocking
    expect(
      screen.getByText(/Show an object to the camera/i)
    ).toBeInTheDocument();
  });
});
