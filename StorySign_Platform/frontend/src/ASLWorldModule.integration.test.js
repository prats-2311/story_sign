import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import ASLWorldModule from "./ASLWorldModule";

// Mock story data for testing
const mockStoryData = {
  title: "The Adventure of the Red Ball",
  sentences: [
    "Once upon a time, there was a bright red ball.",
    "The ball loved to bounce in the sunny park.",
    "Children would come to play with the happy ball.",
    "One day, the ball rolled into a magical forest.",
    "The ball made many new friends among the trees.",
  ],
};

// Mock feedback data for testing
const mockFeedback = {
  feedback:
    "Good hand positioning! Try to make the 'cat' sign more distinct by keeping your fingers closer together.",
  confidence_score: 0.75,
  suggestions: [
    "Focus on hand shape clarity",
    "Maintain consistent signing space",
  ],
  target_sentence: "Once upon a time, there was a bright red ball.",
  received_at: new Date().toISOString(),
  processing_time: 1250,
};

const mockCompletionFeedback = {
  feedback: "Congratulations! You've completed the story!",
  confidence_score: 0.85,
  suggestions: [
    "Great job completing the story!",
    "Try generating a new story to continue practicing",
  ],
  target_sentence: "Story Complete",
  completed: true,
  story_stats: {
    total_sentences: 5,
    completion_time: 45000,
    average_confidence: 0.78,
  },
  received_at: new Date().toISOString(),
};

describe("ASLWorldModule - Task 17.2 Integration Tests", () => {
  const defaultProps = {
    storyData: null,
    currentSentenceIndex: 0,
    latestFeedback: null,
    onStoryGenerate: jest.fn(),
    onPracticeControl: jest.fn(),
    isGeneratingStory: false,
    isProcessingFeedback: false,
    connectionStatus: "connected",
    onFrameCapture: jest.fn(),
    gestureState: "listening",
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock navigator.mediaDevices for webcam access
    Object.defineProperty(navigator, "mediaDevices", {
      writable: true,
      value: {
        getUserMedia: jest.fn().mockResolvedValue({
          getTracks: () => [{ stop: jest.fn() }],
        }),
      },
    });
  });

  describe("Feedback Display and User Interaction", () => {
    test("displays enhanced feedback with all components", async () => {
      render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          currentSentenceIndex={0}
          latestFeedback={mockFeedback}
        />
      );

      // Check feedback display
      expect(screen.getByText("AI Feedback")).toBeInTheDocument();
      expect(screen.getByText(mockFeedback.feedback)).toBeInTheDocument();

      // Check confidence score
      expect(screen.getByText(/Confidence: 75%/)).toBeInTheDocument();

      // Check suggestions
      expect(screen.getByText("Suggestions:")).toBeInTheDocument();
      expect(
        screen.getByText("Focus on hand shape clarity")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Maintain consistent signing space")
      ).toBeInTheDocument();

      // Check processing time
      expect(
        screen.getByText(/Analysis completed in 1250ms/)
      ).toBeInTheDocument();
    });

    test("displays story completion feedback with statistics", async () => {
      render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          currentSentenceIndex={4}
          latestFeedback={mockCompletionFeedback}
          gestureState="completed"
        />
      );

      // Check completion header
      expect(screen.getByText("🎉 Story Complete!")).toBeInTheDocument();
      expect(
        screen.getByText(mockCompletionFeedback.feedback)
      ).toBeInTheDocument();

      // Check overall score
      expect(screen.getByText(/Overall Score: 85%/)).toBeInTheDocument();

      // Check story statistics
      expect(screen.getByText("Practice Summary:")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument(); // total sentences
      expect(screen.getByText("45s")).toBeInTheDocument(); // completion time
      expect(screen.getByText("78%")).toBeInTheDocument(); // average confidence

      // Check completion controls
      expect(screen.getByText("Practice Again")).toBeInTheDocument();
      expect(screen.getByText("New Story")).toBeInTheDocument();
    });

    test("handles error feedback gracefully", async () => {
      const errorFeedback = {
        ...mockFeedback,
        error: true,
        feedback: "Error: Invalid feedback received from server",
      };

      render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          currentSentenceIndex={0}
          latestFeedback={errorFeedback}
        />
      );

      expect(
        screen.getByText(/There was an issue processing your signing/)
      ).toBeInTheDocument();
      expect(screen.getByText(errorFeedback.feedback)).toBeInTheDocument();
    });
  });

  describe("Practice Session Controls", () => {
    test("shows correct control buttons for regular sentences", async () => {
      render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          currentSentenceIndex={1}
          latestFeedback={mockFeedback}
        />
      );

      expect(screen.getByText("Try Again")).toBeInTheDocument();
      expect(screen.getByText(/Next Sentence \(3\/5\)/)).toBeInTheDocument();
      expect(screen.queryByText("Complete Story")).not.toBeInTheDocument();
    });

    test("shows complete story button for last sentence", async () => {
      render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          currentSentenceIndex={4}
          latestFeedback={mockFeedback}
        />
      );

      expect(screen.getByText("Try Again")).toBeInTheDocument();
      expect(screen.getByText("Complete Story")).toBeInTheDocument();
      expect(screen.queryByText(/Next Sentence/)).not.toBeInTheDocument();
    });

    test("calls practice control handlers with correct parameters", async () => {
      const mockOnPracticeControl = jest.fn();

      render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          currentSentenceIndex={1}
          latestFeedback={mockFeedback}
          onPracticeControl={mockOnPracticeControl}
        />
      );

      // Wait for feedback to be displayed
      await waitFor(() => {
        expect(screen.getByText("Try Again")).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText("Next Sentence (3/5)")).toBeInTheDocument();
      });

      // Test Try Again button
      fireEvent.click(screen.getByText("Try Again"));
      expect(mockOnPracticeControl).toHaveBeenCalledWith("try_again", 1);

      // Test Next Sentence button
      fireEvent.click(screen.getByText("Next Sentence (3/5)"));
      expect(mockOnPracticeControl).toHaveBeenCalledWith("next_sentence", 1);
    });

    test("handles completion controls correctly", async () => {
      const mockOnPracticeControl = jest.fn();

      render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          currentSentenceIndex={4}
          latestFeedback={mockCompletionFeedback}
          onPracticeControl={mockOnPracticeControl}
        />
      );

      // Test Practice Again button
      fireEvent.click(screen.getByText("Practice Again"));
      expect(mockOnPracticeControl).toHaveBeenCalledWith("restart_story", 4);

      // Test New Story button
      fireEvent.click(screen.getByText("New Story"));
      expect(mockOnPracticeControl).toHaveBeenCalledWith("new_story", 4);
    });
  });

  describe("Progress Tracking", () => {
    test("displays correct progress information", async () => {
      render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          currentSentenceIndex={2}
        />
      );

      // Check progress text
      expect(screen.getByText("3 of 5")).toBeInTheDocument();

      // Check progress bar (should be 60% filled)
      const progressFill = document.querySelector(".progress-fill");
      expect(progressFill).toHaveStyle("width: 60%");
    });

    test("shows current sentence highlighting", async () => {
      render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          currentSentenceIndex={1}
        />
      );

      // Check that the correct sentence is highlighted in the practice area
      expect(screen.getByText("Practice This Sentence:")).toBeInTheDocument();
      const highlightedSentences = screen.getAllByText(
        mockStoryData.sentences[1]
      );
      expect(highlightedSentences.length).toBeGreaterThan(0); // Should appear in both story display and practice area

      // Check sentence numbering in story display
      const sentences = screen.getAllByText(/\d+\./);
      expect(sentences).toHaveLength(5); // All sentences should be numbered
    });
  });

  describe("Gesture State Indicators", () => {
    test("displays correct gesture state messages", async () => {
      const { rerender } = render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          gestureState="listening"
        />
      );

      expect(screen.getByText("Listening for gestures")).toBeInTheDocument();

      rerender(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          gestureState="detecting"
        />
      );

      expect(
        screen.getByText("Gesture detected - keep signing")
      ).toBeInTheDocument();

      rerender(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          gestureState="analyzing"
          isProcessingFeedback={true}
        />
      );

      expect(screen.getByText("Analyzing your signing...")).toBeInTheDocument();

      rerender(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          gestureState="completed"
        />
      );

      expect(screen.getByText("Story completed!")).toBeInTheDocument();
    });
  });

  describe("Story Generation Mode", () => {
    test("allows switching back to story generation from practice mode", async () => {
      render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          currentSentenceIndex={0}
        />
      );

      // Should be in practice mode initially - check for practice mode elements
      expect(screen.getByText("Practice This Sentence:")).toBeInTheDocument();

      // Click new story button
      fireEvent.click(screen.getByText("Generate New Story"));

      // Should switch back to story generation mode
      expect(screen.getByText("Generate Your Story")).toBeInTheDocument();
      expect(screen.getByText("Scan Object to Start")).toBeInTheDocument();
    });
  });

  describe("Accessibility and User Experience", () => {
    test("disables buttons appropriately during processing", async () => {
      render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          currentSentenceIndex={0}
          latestFeedback={mockFeedback}
          isProcessingFeedback={true}
        />
      );

      expect(screen.getByText("Try Again")).toBeDisabled();
      expect(screen.getByText(/Next Sentence/)).toBeDisabled();
    });

    test("shows appropriate loading states", async () => {
      render(
        <ASLWorldModule
          {...defaultProps}
          storyData={mockStoryData}
          currentSentenceIndex={0}
          isProcessingFeedback={true}
        />
      );

      expect(screen.getByText("Analyzing your signing...")).toBeInTheDocument();
      expect(
        screen.getByText("Please wait while AI analyzes your gesture")
      ).toBeInTheDocument();
    });

    test("handles connection status appropriately", async () => {
      render(
        <ASLWorldModule {...defaultProps} connectionStatus="disconnected" />
      );

      expect(
        screen.getByText("⚠️ Backend connection required for story generation")
      ).toBeInTheDocument();
      expect(screen.getByText("Scan Object to Start")).toBeDisabled();
    });
  });
});
