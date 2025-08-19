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
      expect(screen.getByText(/Connection failed/i)).toBeInTheDocument();
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
      expect(
        screen.getByText(/Backend error: 500 Internal Server Error/i)
      ).toBeInTheDocument();
    });
  });

  test("button shows loading state during request", async () => {
    fetch.mockImplementationOnce(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<App />);
    const button = screen.getByRole("button", { name: /Test Backend/i });

    fireEvent.click(button);

    expect(screen.getByText(/Testing.../i)).toBeInTheDocument();
    expect(button).toBeDisabled();
  });
});
