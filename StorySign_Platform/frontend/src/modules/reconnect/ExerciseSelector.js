import React, { useState, useCallback } from "react";
import Button from "../../components/common/Button";
import Modal from "../../components/common/Modal";
import "./ExerciseSelector.css";

/**
 * ExerciseSelector component for therapeutic exercise selection
 * Provides exercise selection and session setup interface
 */
const ExerciseSelector = ({
  onStartSession,
  webcamStatus,
  webcamError,
  error,
  onClearError,
}) => {
  const [selectedExercise, setSelectedExercise] = useState(null);
  const [showInstructions, setShowInstructions] = useState(false);
  const [isStarting, setIsStarting] = useState(false);

  // Available therapeutic exercises
  const exercises = [
    {
      id: "shoulder_flexion",
      name: "Shoulder Flexion",
      description: "Forward arm raises for shoulder mobility",
      icon: "🤲",
      color: "#3498db",
      difficulty: "Beginner",
      duration: "5-10 minutes",
      targetAreas: ["Shoulders", "Upper Arms"],
      instructions: [
        "Stand with feet shoulder-width apart",
        "Keep arms straight at your sides",
        "Slowly raise both arms forward to shoulder height",
        "Hold for 2 seconds, then lower slowly",
        "Repeat 10-15 times",
      ],
      benefits: [
        "Improves shoulder flexibility",
        "Reduces stiffness",
        "Enhances range of motion",
        "Strengthens shoulder muscles",
      ],
    },
    {
      id: "arm_circles",
      name: "Arm Circles",
      description: "Circular arm movements for joint mobility",
      icon: "🔄",
      color: "#e74c3c",
      difficulty: "Beginner",
      duration: "3-5 minutes",
      targetAreas: ["Shoulders", "Arms"],
      instructions: [
        "Stand with arms extended to the sides",
        "Make small circles with your arms",
        "Gradually increase circle size",
        "Reverse direction after 10 circles",
        "Keep movements smooth and controlled",
      ],
      benefits: [
        "Improves joint mobility",
        "Warms up shoulder muscles",
        "Enhances circulation",
        "Reduces joint stiffness",
      ],
    },
    {
      id: "neck_stretches",
      name: "Neck Stretches",
      description: "Gentle neck movements for cervical mobility",
      icon: "🦢",
      color: "#9b59b6",
      difficulty: "Beginner",
      duration: "5-8 minutes",
      targetAreas: ["Neck", "Upper Spine"],
      instructions: [
        "Sit or stand with good posture",
        "Slowly turn head to the right",
        "Hold for 5 seconds",
        "Return to center and repeat left",
        "Perform gentle up and down movements",
      ],
      benefits: [
        "Relieves neck tension",
        "Improves cervical mobility",
        "Reduces headaches",
        "Enhances posture",
      ],
    },
    {
      id: "torso_twists",
      name: "Torso Twists",
      description: "Spinal rotation exercises for core mobility",
      icon: "🌪️",
      color: "#f39c12",
      difficulty: "Intermediate",
      duration: "8-12 minutes",
      targetAreas: ["Spine", "Core", "Hips"],
      instructions: [
        "Stand with feet hip-width apart",
        "Place hands on hips or cross arms",
        "Slowly rotate torso to the right",
        "Return to center and rotate left",
        "Keep hips facing forward",
      ],
      benefits: [
        "Improves spinal mobility",
        "Strengthens core muscles",
        "Enhances balance",
        "Reduces back stiffness",
      ],
    },
    {
      id: "leg_raises",
      name: "Leg Raises",
      description: "Hip flexion exercises for lower body strength",
      icon: "🦵",
      color: "#27ae60",
      difficulty: "Intermediate",
      duration: "10-15 minutes",
      targetAreas: ["Hips", "Thighs", "Core"],
      instructions: [
        "Stand behind a chair for support",
        "Keep one leg planted firmly",
        "Slowly raise the other leg forward",
        "Hold for 2 seconds at the top",
        "Lower slowly and repeat",
      ],
      benefits: [
        "Strengthens hip flexors",
        "Improves balance",
        "Enhances core stability",
        "Increases leg strength",
      ],
    },
    {
      id: "balance_training",
      name: "Balance Training",
      description: "Static and dynamic balance exercises",
      icon: "⚖️",
      color: "#e67e22",
      difficulty: "Advanced",
      duration: "15-20 minutes",
      targetAreas: ["Full Body", "Core", "Legs"],
      instructions: [
        "Start with single-leg stands",
        "Progress to eyes-closed balance",
        "Add arm movements while balancing",
        "Try heel-to-toe walking",
        "Use support as needed",
      ],
      benefits: [
        "Improves proprioception",
        "Reduces fall risk",
        "Enhances coordination",
        "Strengthens stabilizing muscles",
      ],
    },
  ];

  // Handle exercise selection
  const handleExerciseSelect = useCallback(exercise => {
    setSelectedExercise(exercise);
  }, []);

  // Handle starting therapy session
  const handleStartTherapy = useCallback(async () => {
    if (!selectedExercise) return;

    setIsStarting(true);
    try {
      await onStartSession(selectedExercise);
    } catch (error) {
      console.error("Error starting therapy session:", error);
    } finally {
      setIsStarting(false);
    }
  }, [selectedExercise, onStartSession]);

  // Handle showing instructions
  const handleShowInstructions = useCallback(() => {
    setShowInstructions(true);
  }, []);

  // Handle closing instructions
  const handleCloseInstructions = useCallback(() => {
    setShowInstructions(false);
  }, []);

  // Get difficulty color
  const getDifficultyColor = difficulty => {
    switch (difficulty) {
      case "Beginner":
        return "#27ae60";
      case "Intermediate":
        return "#f39c12";
      case "Advanced":
        return "#e74c3c";
      default:
        return "#95a5a6";
    }
  };

  // Check if system is ready for therapy - backend connects automatically
  const isSystemReady =
    webcamStatus === "active" || webcamStatus === "inactive";

  return (
    <div className="exercise-selector">
      <div className="selector-header">
        <h2>Choose a Therapeutic Exercise</h2>
        <p>
          Select an exercise below to begin your movement analysis and therapy
          session.
        </p>

        <div className="header-actions">
          <Button
            variant="secondary"
            onClick={handleShowInstructions}
            ariaLabel="Show therapy instructions"
          >
            📖 Instructions
          </Button>
        </div>
      </div>

      {/* System Status */}
      <div className="system-status" role="status" aria-live="polite">
        <div className="status-item connected">
          <span className="status-icon">✅</span>
          <span>Backend: Ready</span>
        </div>

        <div className={`status-item ${webcamStatus}`}>
          <span className="status-icon">
            {webcamStatus === "active"
              ? "📹"
              : webcamStatus === "initializing"
              ? "⏳"
              : "📷"}
          </span>
          <span>Camera: {webcamStatus}</span>
        </div>
      </div>

      {/* Error Display */}
      {(error || webcamError) && (
        <div className="error-display" role="alert">
          <div className="error-content">
            <h3>⚠️ {(error || webcamError).type}</h3>
            <p>{(error || webcamError).message}</p>
            {(error || webcamError).userAction && (
              <p className="error-action">
                <strong>Action needed:</strong>{" "}
                {(error || webcamError).userAction}
              </p>
            )}
            <Button
              variant="secondary"
              onClick={onClearError}
              ariaLabel="Dismiss error message"
            >
              Dismiss
            </Button>
          </div>
        </div>
      )}

      {/* Exercise Selection Grid */}
      <div className="exercises-grid">
        {exercises.map(exercise => (
          <div
            key={exercise.id}
            className={`exercise-card ${
              selectedExercise?.id === exercise.id ? "selected" : ""
            }`}
            onClick={() => handleExerciseSelect(exercise)}
            role="button"
            tabIndex={0}
            aria-pressed={selectedExercise?.id === exercise.id}
            onKeyDown={e => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleExerciseSelect(exercise);
              }
            }}
          >
            <div
              className="exercise-icon"
              style={{ backgroundColor: exercise.color }}
            >
              {exercise.icon}
            </div>

            <div className="exercise-header">
              <h3>{exercise.name}</h3>
              <div
                className="difficulty-badge"
                style={{
                  backgroundColor: getDifficultyColor(exercise.difficulty),
                }}
              >
                {exercise.difficulty}
              </div>
            </div>

            <p className="exercise-description">{exercise.description}</p>

            <div className="exercise-meta">
              <div className="meta-item">
                <span className="meta-icon">⏱️</span>
                <span>{exercise.duration}</span>
              </div>
              <div className="meta-item">
                <span className="meta-icon">🎯</span>
                <span>{exercise.targetAreas.join(", ")}</span>
              </div>
            </div>

            {selectedExercise?.id === exercise.id && (
              <div className="exercise-details">
                <div className="instructions-preview">
                  <h4>Instructions:</h4>
                  <ol>
                    {exercise.instructions
                      .slice(0, 3)
                      .map((instruction, index) => (
                        <li key={index}>{instruction}</li>
                      ))}
                    {exercise.instructions.length > 3 && (
                      <li>
                        ... and {exercise.instructions.length - 3} more steps
                      </li>
                    )}
                  </ol>
                </div>

                <div className="benefits-preview">
                  <h4>Benefits:</h4>
                  <ul>
                    {exercise.benefits.slice(0, 2).map((benefit, index) => (
                      <li key={index}>{benefit}</li>
                    ))}
                    {exercise.benefits.length > 2 && <li>... and more</li>}
                  </ul>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Start Therapy Button */}
      {selectedExercise && (
        <div className="start-therapy-section">
          <div className="selected-exercise-summary">
            <span
              className="exercise-icon"
              style={{ backgroundColor: selectedExercise.color }}
            >
              {selectedExercise.icon}
            </span>
            <div>
              <h3>Ready for: {selectedExercise.name}</h3>
              <p>{selectedExercise.description}</p>
              <div className="summary-meta">
                <span className="duration">
                  Duration: {selectedExercise.duration}
                </span>
                <span
                  className="difficulty"
                  style={{
                    color: getDifficultyColor(selectedExercise.difficulty),
                  }}
                >
                  {selectedExercise.difficulty} Level
                </span>
              </div>
            </div>
          </div>

          <Button
            variant="primary"
            onClick={handleStartTherapy}
            disabled={!isSystemReady || isStarting}
            loading={isStarting}
            ariaLabel={`Start ${selectedExercise.name} therapy session`}
            className="start-therapy-button"
          >
            {isStarting
              ? "Starting Session..."
              : `Start ${selectedExercise.name} Session`}
          </Button>

          {!isSystemReady && (
            <p className="system-not-ready">
              Please ensure your camera is ready before starting.
            </p>
          )}
        </div>
      )}

      {/* Instructions Modal */}
      <Modal
        isOpen={showInstructions}
        onClose={handleCloseInstructions}
        title="Reconnect Therapy Instructions"
        className="instructions-modal"
      >
        <div className="instructions-content">
          <section>
            <h3>🎯 How It Works</h3>
            <p>
              Reconnect uses advanced pose detection to analyze your movements
              and provide quantitative feedback for physical therapy and
              rehabilitation exercises.
            </p>
          </section>

          <section>
            <h3>📋 Getting Started</h3>
            <ol>
              <li>Choose an exercise appropriate for your fitness level</li>
              <li>Read the exercise instructions and benefits</li>
              <li>Ensure your camera can see your full body</li>
              <li>Click "Start Session" to begin movement analysis</li>
            </ol>
          </section>

          <section>
            <h3>💡 Therapy Tips</h3>
            <ul>
              <li>Ensure good lighting and clear camera view</li>
              <li>Wear contrasting clothing for better detection</li>
              <li>Start slowly and focus on proper form</li>
              <li>Listen to your body and don't push through pain</li>
              <li>Use the real-time feedback to improve technique</li>
            </ul>
          </section>

          <section>
            <h3>⚠️ Safety Guidelines</h3>
            <ul>
              <li>Consult your healthcare provider before starting</li>
              <li>Stop immediately if you experience pain</li>
              <li>Stay within your comfortable range of motion</li>
              <li>Use support (chair, wall) when needed</li>
              <li>Progress gradually over time</li>
            </ul>
          </section>

          <section>
            <h3>🔒 Privacy & Data</h3>
            <ul>
              <li>Movement analysis is processed locally when possible</li>
              <li>No video recordings are stored permanently</li>
              <li>Only anonymized progress metrics are saved</li>
              <li>You can end any session at any time</li>
            </ul>
          </section>
        </div>
      </Modal>
    </div>
  );
};

export default ExerciseSelector;
