/**
 * Test Task 17.1: Practice Session Controls and State Management
 * Tests for frontend practice session control functionality
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import ASLWorldModule from "./ASLWorldModule";

// Mock WebSocket functionality
const mockSendPracticeControl = jest.fn();
const mockVideoStreamingRef = {
  current: {
    sendPracticeControl: mockSendPracticeControl,
  },
};

// Mock story data for testing
const mockStoryData = {
  title: "Test Story",
  sentences: [
    "The cat sat on the mat.",
    "The dog ran in the park.",
    "The bird flew in the sky.",
  ],
};

describe("Task 17.1: Practice Session Controls", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("should display practice controls when story is available", () => {
    render(
      <ASLWorldModule
        storyData={mockStoryData}
        currentSentenceIndex={0}
        connectionStatus="connected"
        gestureState="listening"
      />
    );

    // Check if practice mode is displayed
    expect(screen.getByText("Practice Story: Test Story")).toBeInTheDocument();
    expect(screen.getByText("The cat sat on the mat.")).toBeInTheDocument();
  });

  test("should show correct gesture state indicators", () => {
    const { rerender } = render(
      <ASLWorldModule
        storyData={mockStoryData}
        currentSentenceIndex={0}
        connectionStatus="connected"
        gestureState="listening"
      />
    );

    // Check listening state
    expect(screen.getByText("Listening for gestures")).toBeInTheDocument();

    // Change to detecting state
    rerender(
      <ASLWorldModule
        storyData={mockStoryData}
        currentSentenceIndex={0}
        connectionStatus="connected"
        gestureState="detecting"
      />
    );

    expect(
      screen.getByText("Gesture detected - keep signing")
    ).toBeInTheDocument();

    // Change to analyzing state
    rerender(
      <ASLWorldModule
        storyData={mockStoryData}
        currentSentenceIndex={0}
        connectionStatus="connected"
        gestureState="analyzing"
      />
    );

    expect(screen.getByText("Analyzing your gesture")).toBeInTheDocument();
  });

  test("should display feedback when available", () => {
    const mockFeedback = {
      feedback:
        "Good hand positioning! Try to make the 'cat' sign more distinct.",
      confidence_score: 0.75,
      suggestions: [
        "Focus on hand shape clarity",
        "Maintain consistent signing space",
      ],
    };

    render(
      <ASLWorldModule
        storyData={mockStoryData}
        currentSentenceIndex={0}
        latestFeedback={mockFeedback}
        connectionStatus="connected"
        gestureState="listening"
      />
    );

    // Check if feedback is displayed
    expect(
      screen.getByText(
        "Good hand positioning! Try to make the 'cat' sign more distinct."
      )
    ).toBeInTheDocument();
    expect(screen.getByText("Confidence: 75%")).toBeInTheDocument();
    expect(screen.getByText("Focus on hand shape clarity")).toBeInTheDocument();
  });

  test("should show control buttons when feedback is available", () => {
    const mockFeedback = {
      feedback: "Great job!",
      confidence_score: 0.85,
    };

    render(
      <ASLWorldModule
        storyData={mockStoryData}
        currentSentenceIndex={0}
        latestFeedback={mockFeedback}
        connectionStatus="connected"
        gestureState="listening"
      />
    );

    // Check if control buttons are displayed
    expect(screen.getByText("Try Again")).toBeInTheDocument();
    expect(screen.getByText("Next Sentence")).toBeInTheDocument();
  });

  test("should show complete story button on last sentence", () => {
    const mockFeedback = {
      feedback: "Excellent work!",
      confidence_score: 0.9,
    };

    render(
      <ASLWorldModule
        storyData={mockStoryData}
        currentSentenceIndex={2} // Last sentence
        latestFeedback={mockFeedback}
        connectionStatus="connected"
        gestureState="listening"
      />
    );

    // Check if complete story button is displayed instead of next sentence
    expect(screen.getByText("Try Again")).toBeInTheDocument();
    expect(screen.getByText("Complete Story")).toBeInTheDocument();
    expect(screen.queryByText("Next Sentence")).not.toBeInTheDocument();
  });

  test("should highlight current sentence correctly", () => {
    render(
      <ASLWorldModule
        storyData={mockStoryData}
        currentSentenceIndex={1}
        connectionStatus="connected"
        gestureState="listening"
      />
    );

    // Check if sentences have correct classes
    const sentences = screen.getAllByText(/The .* (sat|ran|flew)/);

    // First sentence should be completed
    expect(sentences[0].closest(".story-sentence")).toHaveClass("completed");

    // Second sentence should be current
    expect(sentences[1].closest(".story-sentence")).toHaveClass("current");

    // Third sentence should be neither
    expect(sentences[2].closest(".story-sentence")).not.toHaveClass("current");
    expect(sentences[2].closest(".story-sentence")).not.toHaveClass(
      "completed"
    );
  });

  test("should show processing indicator when analyzing", () => {
    render(
      <ASLWorldModule
        storyData={mockStoryData}
        currentSentenceIndex={0}
        isProcessingFeedback={true}
        connectionStatus="connected"
        gestureState="analyzing"
      />
    );

    // Check if processing indicator is shown
    expect(screen.getByText("Analyzing your signing...")).toBeInTheDocument();
    expect(
      screen.getByText("Please wait while AI analyzes your gesture")
    ).toBeInTheDocument();
  });

  test("should show connection warning when disconnected", () => {
    render(
      <ASLWorldModule
        connectionStatus="disconnected"
        gestureState="listening"
      />
    );

    // Check if connection warning is displayed
    expect(
      screen.getByText("⚠️ Backend connection required for story generation")
    ).toBeInTheDocument();
  });

  test("should disable scan button when generating story", () => {
    render(
      <ASLWorldModule
        isGeneratingStory={true}
        connectionStatus="connected"
        gestureState="listening"
      />
    );

    // Check if scan button is disabled and shows loading
    const scanButton = screen.getByRole("button");
    expect(scanButton).toBeDisabled();
    expect(screen.getByText("Generating Story...")).toBeInTheDocument();
  });
});

describe("Practice Control Integration", () => {
  test("should call onPracticeControl when buttons are clicked", () => {
    const mockOnPracticeControl = jest.fn();
    const mockFeedback = {
      feedback: "Good work!",
      confidence_score: 0.8,
    };

    render(
      <ASLWorldModule
        storyData={mockStoryData}
        currentSentenceIndex={0}
        latestFeedback={mockFeedback}
        onPracticeControl={mockOnPracticeControl}
        connectionStatus="connected"
        gestureState="listening"
      />
    );

    // Click Try Again button
    fireEvent.click(screen.getByText("Try Again"));
    expect(mockOnPracticeControl).toHaveBeenCalledWith("try_again", 0);

    // Click Next Sentence button
    fireEvent.click(screen.getByText("Next Sentence"));
    expect(mockOnPracticeControl).toHaveBeenCalledWith("next_sentence", 0);
  });

  test("should call onPracticeControl for complete story", () => {
    const mockOnPracticeControl = jest.fn();
    const mockFeedback = {
      feedback: "Perfect!",
      confidence_score: 0.95,
    };

    render(
      <ASLWorldModule
        storyData={mockStoryData}
        currentSentenceIndex={2} // Last sentence
        latestFeedback={mockFeedback}
        onPracticeControl={mockOnPracticeControl}
        connectionStatus="connected"
        gestureState="listening"
      />
    );

    // Click Complete Story button
    fireEvent.click(screen.getByText("Complete Story"));
    expect(mockOnPracticeControl).toHaveBeenCalledWith("complete_story", 2);
  });
});
