import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import ExerciseSelector from "./ExerciseSelector";

// Mock the common components
jest.mock(
  "../../components/common/Button",
  () =>
    ({ children, onClick, disabled, loading, variant, ariaLabel, className }) =>
      (
        <button
          onClick={onClick}
          disabled={disabled || loading}
          className={`btn ${variant} ${className}`}
          aria-label={ariaLabel}
        >
          {loading ? "Loading..." : children}
        </button>
      )
);

jest.mock(
  "../../components/common/Modal",
  () =>
    ({ isOpen, onClose, title, children, className }) =>
      isOpen ? (
        <div className={`modal ${className}`} data-testid="modal">
          <div className="modal-header">
            <h2>{title}</h2>
            <button onClick={onClose}>×</button>
          </div>
          <div className="modal-content">{children}</div>
        </div>
      ) : null
);

describe("ExerciseSelector", () => {
  const defaultProps = {
    onStartSession: jest.fn(),
    connectionStatus: "connected",
    webcamStatus: "active",
    webcamError: null,
    error: null,
    onClearError: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders exercise selector with header", () => {
    render(<ExerciseSelector {...defaultProps} />);

    expect(
      screen.getByText("Choose a Therapeutic Exercise")
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Select an exercise below to begin your movement analysis and therapy session."
      )
    ).toBeInTheDocument();
  });

  test("displays system status correctly", () => {
    render(<ExerciseSelector {...defaultProps} />);

    expect(screen.getByText("Backend: connected")).toBeInTheDocument();
    expect(screen.getByText("Camera: active")).toBeInTheDocument();
  });

  test("shows error when present", () => {
    const errorProps = {
      ...defaultProps,
      error: { type: "TEST_ERROR", message: "Test error message" },
    };

    render(<ExerciseSelector {...errorProps} />);

    expect(screen.getByText("⚠️ TEST_ERROR")).toBeInTheDocument();
    expect(screen.getByText("Test error message")).toBeInTheDocument();
  });

  test("renders exercise cards", () => {
    render(<ExerciseSelector {...defaultProps} />);

    // Check for some of the exercise names
    expect(screen.getByText("Shoulder Flexion")).toBeInTheDocument();
    expect(screen.getByText("Arm Circles")).toBeInTheDocument();
    expect(screen.getByText("Balance Training")).toBeInTheDocument();
  });

  test("allows exercise selection", () => {
    render(<ExerciseSelector {...defaultProps} />);

    const shoulderExercise = screen
      .getByText("Shoulder Flexion")
      .closest(".exercise-card");
    fireEvent.click(shoulderExercise);

    // Should show the start session section
    expect(screen.getByText("Ready for: Shoulder Flexion")).toBeInTheDocument();
  });

  test("shows instructions modal when clicked", () => {
    render(<ExerciseSelector {...defaultProps} />);

    const instructionsButton = screen.getByText("📖 Instructions");
    fireEvent.click(instructionsButton);

    expect(screen.getByTestId("modal")).toBeInTheDocument();
    expect(
      screen.getByText("Reconnect Therapy Instructions")
    ).toBeInTheDocument();
  });

  test("calls onStartSession when start button is clicked", () => {
    render(<ExerciseSelector {...defaultProps} />);

    // Select an exercise first
    const shoulderExercise = screen
      .getByText("Shoulder Flexion")
      .closest(".exercise-card");
    fireEvent.click(shoulderExercise);

    // Click start session
    const startButton = screen.getByText(/Start.*Session/);
    fireEvent.click(startButton);

    expect(defaultProps.onStartSession).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "shoulder_flexion",
        name: "Shoulder Flexion",
      })
    );
  });

  test("disables start button when system not ready", () => {
    const notReadyProps = {
      ...defaultProps,
      connectionStatus: "disconnected",
    };

    render(<ExerciseSelector {...notReadyProps} />);

    // Select an exercise
    const shoulderExercise = screen
      .getByText("Shoulder Flexion")
      .closest(".exercise-card");
    fireEvent.click(shoulderExercise);

    // Start button should be disabled
    const startButton = screen.getByText(/Start.*Session/);
    expect(startButton).toBeDisabled();
  });

  test("shows system not ready message", () => {
    const notReadyProps = {
      ...defaultProps,
      connectionStatus: "disconnected",
    };

    render(<ExerciseSelector {...notReadyProps} />);

    // Select an exercise to show the start section
    const shoulderExercise = screen
      .getByText("Shoulder Flexion")
      .closest(".exercise-card");
    fireEvent.click(shoulderExercise);

    expect(
      screen.getByText(
        "Please ensure your camera and backend connection are ready before starting."
      )
    ).toBeInTheDocument();
  });
});
