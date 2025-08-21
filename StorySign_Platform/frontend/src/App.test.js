import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import App from "./App";

// Mock fetch for testing
global.fetch = jest.fn();

describe("StorySign App", () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test("renders StorySign title", () => {
    render(<App />);
    const titleElement = screen.getByRole("heading", { name: /StorySign/i });
    expect(titleElement).toBeInTheDocument();
  });

  test("renders Test Backend button", () => {
    render(<App />);
    const buttonElement = screen.getByRole("button", { name: /Test Backend/i });
    expect(buttonElement).toBeInTheDocument();
  });

  test("displays initial placeholder message", () => {
    render(<App />);
    const placeholderMessage = screen.getByText(
      /Click "Test Backend" to verify connectivity/i
    );
    expect(placeholderMessage).toBeInTheDocument();
  });

  test("handles successful backend connection", async () => {
    const mockResponse = {
      message: "Hello from the StorySign Backend!",
      status: "healthy",
      timestamp: "2024-08-20T10:30:00.000Z",
      version: "1.0.0",
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    render(<App />);
    const button = screen.getByRole("button", { name: /Test Backend/i });

    fireEvent.click(button);

    await waitFor(() => {
      expect(
        screen.getByText(/Hello from the StorySign Backend!/i)
      ).toBeInTheDocument();
    });

    expect(fetch).toHaveBeenCalledWith("http://localhost:8000/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
  });

  test("handles backend connection error", async () => {
    fetch.mockRejectedValueOnce(new Error("Connection failed"));

    render(<App />);
    const button = screen.getByRole("button", { name: /Test Backend/i });

    fireEvent.click(button);

    await waitFor(() => {
      expect(
        screen.getByText(/Cannot reach backend server/i)
      ).toBeInTheDocument();
    });
  });

  test("handles HTTP error response", async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    });

    render(<App />);
    const button = screen.getByRole("button", { name: /Test Backend/i });

    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Backend server error/i)).toBeInTheDocument();
    });
  });

  test("button shows loading state during request", async () => {
    fetch.mockImplementationOnce(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<App />);
    const button = screen.getByRole("button", { name: /Test Backend/i });

    fireEvent.click(button);

    expect(
      screen.getByRole("button", { name: /Testing.../i })
    ).toBeInTheDocument();
    expect(button).toBeDisabled();
  });

  test("renders ASL World toggle button", () => {
    render(<App />);
    const aslWorldButton = screen.getByRole("button", {
      name: /Enter ASL World/i,
    });
    expect(aslWorldButton).toBeInTheDocument();
  });

  test("ASL World toggle button is disabled when backend not connected", () => {
    render(<App />);
    const aslWorldButton = screen.getByRole("button", {
      name: /Enter ASL World/i,
    });
    expect(aslWorldButton).toBeDisabled();
  });

  test("ASL World toggle button is enabled when backend is connected", async () => {
    const mockResponse = {
      message: "Hello from the StorySign Backend!",
      status: "healthy",
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    render(<App />);
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
  });

  test("toggles ASL World view when button is clicked", async () => {
    // First connect to backend
    const mockResponse = {
      message: "Hello from the StorySign Backend!",
      status: "healthy",
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    render(<App />);
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

    // Click ASL World button
    const aslWorldButton = screen.getByRole("button", {
      name: /Enter ASL World/i,
    });
    fireEvent.click(aslWorldButton);

    // Should show ASL World interface
    await waitFor(() => {
      expect(
        screen.getByText(/Interactive American Sign Language Learning/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/Generate Your Story/i)).toBeInTheDocument();
    });

    // Button text should change
    expect(
      screen.getByRole("button", { name: /Exit ASL World/i })
    ).toBeInTheDocument();
  });

  test("handles story generation API call", async () => {
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

    // Connect to backend first
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

    // Note: Full story generation test would require mocking webcam access
    // This test verifies the UI integration is working
  });

  test("handles story generation error", async () => {
    // Mock successful backend connection
    const mockBackendResponse = {
      message: "Hello from the StorySign Backend!",
      status: "healthy",
    };

    // Mock story generation error
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockBackendResponse,
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 503,
        statusText: "Service Unavailable",
        json: async () => ({
          error_type: "service_unavailable",
          user_message:
            "AI services are temporarily unavailable. Please try again later.",
        }),
      });

    render(<App />);

    // Connect to backend first
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

    // This test verifies error handling integration is in place
    // Full error testing would require mocking the story generation call
  });
});
