import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe, toHaveNoViolations } from "jest-axe";
import ASLWorldPage from "./ASLWorldPage";

expect.extend(toHaveNoViolations);

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock MediaDevices API
const mockGetUserMedia = jest.fn();
Object.defineProperty(navigator, "mediaDevices", {
  writable: true,
  value: {
    getUserMedia: mockGetUserMedia,
  },
});

// Mock HTMLVideoElement methods
Object.defineProperty(HTMLVideoElement.prototype, "play", {
  writable: true,
  value: jest.fn().mockResolvedValue(undefined),
});

Object.defineProperty(HTMLVideoElement.prototype, "pause", {
  writable: true,
  value: jest.fn(),
});

describe("ASLWorldPage Integration Tests", () => {
  // Helper function to navigate to word selection and click Cat
  const selectCatWord = async (user, screen) => {
    const wordTabButton = screen.getByText("Choose a Word");
    await user.click(wordTabButton);

    await waitFor(() => {
      expect(screen.getByText("Cat")).toBeInTheDocument();
    });

    const catWordButton = screen.getByText("Cat");
    await user.click(catWordButton);
  };

  const defaultProps = {
    connectionStatus: "connected",
    webcamActive: false,
    streamingActive: false,
    onFrameCapture: jest.fn(),
    videoStreamingRef: { current: null },
    processedFrameData: null,
    streamingConnectionStatus: "disconnected",
    optimizationSettings: {},
    onOptimizationChange: jest.fn(),
    onConnectionChange: jest.fn(),
    onProcessedFrame: jest.fn(),
    onError: jest.fn(),
    onRetryConnection: jest.fn(),
    toggleWebcam: jest.fn(),
    toggleStreaming: jest.fn(),
    testBackendConnection: jest.fn(),
  };

  const mockStoryData = {
    amateur: {
      title: "Simple Cat Story",
      sentences: ["The cat sits.", "The cat runs."],
    },
    normal: {
      title: "Normal Cat Story",
      sentences: ["The orange cat sits quietly.", "The cat runs quickly home."],
    },
    mid_level: {
      title: "Mid-Level Cat Story",
      sentences: [
        "The fluffy orange cat sits quietly on the windowsill.",
        "When startled, the cat runs quickly toward home.",
      ],
    },
    difficult: {
      title: "Difficult Cat Story",
      sentences: [
        "The magnificent orange tabby cat sits quietly and patiently on the sunny windowsill.",
        "When suddenly startled by a loud noise, the graceful cat runs quickly and purposefully toward the safety of home.",
      ],
    },
    expert: {
      title: "Expert Cat Story",
      sentences: [
        "The magnificent, fluffy orange tabby cat with bright green eyes sits quietly and patiently on the warm, sunny windowsill, watching the world outside with intense curiosity.",
        "When suddenly startled by an unexpected loud noise from the street below, the graceful and agile cat immediately runs quickly and purposefully toward the familiar safety and comfort of home.",
      ],
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockClear();
    mockGetUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: jest.fn() }],
    });
  });

  test("complete user workflow: story generation to practice completion", async () => {
    const user = userEvent.setup();

    // Mock successful story generation
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        stories: mockStoryData,
      }),
    });

    render(<ASLWorldPage {...defaultProps} />);

    // 1. Initial state - should show story generation
    expect(screen.getByText("Create Your ASL Story")).toBeInTheDocument();
    expect(screen.getByText("Scan Object")).toBeInTheDocument();

    // 2. Generate story using simple word
    await selectCatWord(user, screen);

    // Wait for story generation to complete
    await waitFor(() => {
      expect(
        screen.getByText("Choose Your Challenge Level")
      ).toBeInTheDocument();
    });

    // 3. Select story difficulty
    const midLevelButton = screen.getByLabelText(
      /Select Mid-Level difficulty story/
    );
    await user.click(midLevelButton);

    // Should now be in practice view
    await waitFor(() => {
      expect(screen.getByText(/Practice Story:/)).toBeInTheDocument();
      expect(screen.getByText("Mid-Level Cat Story")).toBeInTheDocument();
    });

    // 4. Start practice session
    const startPracticeButton = screen.getByText("Start Practice Session");
    await user.click(startPracticeButton);

    expect(defaultProps.toggleWebcam).toHaveBeenCalled();
  });

  test("handles story generation errors gracefully", async () => {
    const user = userEvent.setup();

    // Mock failed story generation
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: async () => ({
        success: false,
        message: "AI service temporarily unavailable",
      }),
    });

    render(<ASLWorldPage {...defaultProps} />);

    // Try to generate story
    const catWordButton = screen.getByText("Cat");
    await user.click(catWordButton);

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/Story Generation Error/)).toBeInTheDocument();
      expect(
        screen.getByText(/AI service temporarily unavailable/)
      ).toBeInTheDocument();
    });

    // Should be able to dismiss error
    const dismissButton = screen.getByLabelText("Dismiss error message");
    await user.click(dismissButton);

    await waitFor(() => {
      expect(
        screen.queryByText(/Story Generation Error/)
      ).not.toBeInTheDocument();
    });
  });

  test("supports keyboard navigation throughout workflow", async () => {
    const user = userEvent.setup();

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        stories: mockStoryData,
      }),
    });

    render(<ASLWorldPage {...defaultProps} />);

    // Navigate using keyboard
    await user.tab(); // Should focus first interactive element
    await user.tab(); // Navigate to word selection tab
    await user.keyboard("{Enter}"); // Activate word selection

    // Navigate to a word and select it
    await user.tab(); // First word
    await user.keyboard("{Enter}"); // Select Cat

    // Wait for story selection
    await waitFor(() => {
      expect(
        screen.getByText("Choose Your Challenge Level")
      ).toBeInTheDocument();
    });

    // Navigate through difficulty cards using keyboard
    await user.tab(); // First difficulty card button
    await user.keyboard("{Enter}"); // Select amateur difficulty

    await waitFor(() => {
      expect(screen.getByText(/Practice Story:/)).toBeInTheDocument();
    });
  });

  test("provides proper ARIA announcements for state changes", async () => {
    const user = userEvent.setup();

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        stories: mockStoryData,
      }),
    });

    render(<ASLWorldPage {...defaultProps} />);

    // Check initial connection status announcement
    const connectionStatus =
      screen.getByLabelText(/Connection status/i) ||
      screen.getByText("Connected");
    expect(connectionStatus).toBeInTheDocument();

    // Generate story and check for progress announcements
    const catWordButton = screen.getByText("Cat");
    await user.click(catWordButton);

    // Should show loading state with proper ARIA
    expect(screen.getByText("Generating stories...")).toBeInTheDocument();

    await waitFor(() => {
      expect(
        screen.getByText("Choose Your Challenge Level")
      ).toBeInTheDocument();
    });
  });

  test("handles practice session state management correctly", async () => {
    const user = userEvent.setup();

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        stories: mockStoryData,
      }),
    });

    const mockVideoStreamingRef = {
      current: {
        sendPracticeControl: jest.fn().mockReturnValue(true),
        framesSent: 0,
        framesReceived: 0,
      },
    };

    render(
      <ASLWorldPage
        {...defaultProps}
        videoStreamingRef={mockVideoStreamingRef}
      />
    );

    // Generate and select story
    const catWordButton = screen.getByText("Cat");
    await user.click(catWordButton);

    await waitFor(() => {
      expect(
        screen.getByText("Choose Your Challenge Level")
      ).toBeInTheDocument();
    });

    const amateurButton = screen.getByLabelText(
      /Select Amateur difficulty story/
    );
    await user.click(amateurButton);

    await waitFor(() => {
      expect(screen.getByText(/Practice Story:/)).toBeInTheDocument();
    });

    // Start practice
    const startPracticeButton = screen.getByText("Start Practice Session");
    await user.click(startPracticeButton);

    // Should show gesture status
    await waitFor(() => {
      expect(
        screen.getByText(/Ready to detect your signing/)
      ).toBeInTheDocument();
    });
  });

  test("passes accessibility tests for all views", async () => {
    const user = userEvent.setup();

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        stories: mockStoryData,
      }),
    });

    const { container } = render(<ASLWorldPage {...defaultProps} />);

    // Test story generation view
    let results = await axe(container);
    expect(results).toHaveNoViolations();

    // Generate story to test selection view
    const catWordButton = screen.getByText("Cat");
    await user.click(catWordButton);

    await waitFor(() => {
      expect(
        screen.getByText("Choose Your Challenge Level")
      ).toBeInTheDocument();
    });

    // Test story selection view
    results = await axe(container);
    expect(results).toHaveNoViolations();

    // Select story to test practice view
    const amateurButton = screen.getByLabelText(
      /Select Amateur difficulty story/
    );
    await user.click(amateurButton);

    await waitFor(() => {
      expect(screen.getByText(/Practice Story:/)).toBeInTheDocument();
    });

    // Test practice view
    results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test("handles back navigation correctly", async () => {
    const user = userEvent.setup();

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        stories: mockStoryData,
      }),
    });

    render(<ASLWorldPage {...defaultProps} />);

    // Generate story
    const catWordButton = screen.getByText("Cat");
    await user.click(catWordButton);

    await waitFor(() => {
      expect(
        screen.getByText("Choose Your Challenge Level")
      ).toBeInTheDocument();
    });

    // Go back to generation
    const backButton = screen.getByText("← Generate Different Stories");
    await user.click(backButton);

    await waitFor(() => {
      expect(screen.getByText("Create Your ASL Story")).toBeInTheDocument();
    });
  });

  test("handles practice control actions", async () => {
    const user = userEvent.setup();

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        stories: mockStoryData,
      }),
    });

    const mockVideoStreamingRef = {
      current: {
        sendPracticeControl: jest.fn().mockReturnValue(true),
      },
    };

    render(
      <ASLWorldPage
        {...defaultProps}
        videoStreamingRef={mockVideoStreamingRef}
        streamingActive={true}
      />
    );

    // Navigate to practice view
    const catWordButton = screen.getByText("Cat");
    await user.click(catWordButton);

    await waitFor(() => {
      expect(
        screen.getByText("Choose Your Challenge Level")
      ).toBeInTheDocument();
    });

    const amateurButton = screen.getByLabelText(
      /Select Amateur difficulty story/
    );
    await user.click(amateurButton);

    await waitFor(() => {
      expect(screen.getByText(/Practice Story:/)).toBeInTheDocument();
    });

    // Test new story action
    const newStoryButton = screen.getByText("New Story");
    await user.click(newStoryButton);

    expect(
      mockVideoStreamingRef.current.sendPracticeControl
    ).toHaveBeenCalledWith("new_story", expect.any(Object));

    // Should return to story generation
    await waitFor(() => {
      expect(screen.getByText("Create Your ASL Story")).toBeInTheDocument();
    });
  });
});
