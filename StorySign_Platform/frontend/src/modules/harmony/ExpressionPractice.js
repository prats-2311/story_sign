import React, { useState, useCallback } from "react";
import Button from "../../components/common/Button";
import Modal from "../../components/common/Modal";
import "./ExpressionPractice.css";

/**
 * ExpressionPractice component for facial expression detection and practice
 * Provides emotion selection and session setup interface
 */
const ExpressionPractice = ({
  onStartSession,
  webcamStatus,
  webcamError,
  error,
  onClearError,
}) => {
  const [selectedEmotion, setSelectedEmotion] = useState(null);
  const [showInstructions, setShowInstructions] = useState(false);
  const [isStarting, setIsStarting] = useState(false);

  // Available emotions for practice
  const emotions = [
    {
      id: "happy",
      name: "Happy",
      description: "Practice showing joy and happiness",
      icon: "😊",
      color: "#ffd93d",
      tips: [
        "Smile with your eyes (Duchenne smile)",
        "Raise the corners of your mouth",
        "Relax your forehead",
        "Let the joy show naturally",
      ],
    },
    {
      id: "sad",
      name: "Sad",
      description: "Practice expressing sadness appropriately",
      icon: "😢",
      color: "#74b9ff",
      tips: [
        "Lower the corners of your mouth slightly",
        "Let your eyes show the emotion",
        "Relax your facial muscles",
        "Don't exaggerate the expression",
      ],
    },
    {
      id: "surprised",
      name: "Surprised",
      description: "Practice showing surprise and wonder",
      icon: "😮",
      color: "#fd79a8",
      tips: [
        "Raise your eyebrows",
        "Open your eyes wider",
        "Drop your jaw slightly",
        "Keep the expression brief and natural",
      ],
    },
    {
      id: "angry",
      name: "Angry",
      description: "Practice controlled expression of anger",
      icon: "😠",
      color: "#e17055",
      tips: [
        "Lower your brow slightly",
        "Tighten your lips",
        "Keep control of the intensity",
        "Practice healthy expression",
      ],
    },
    {
      id: "fearful",
      name: "Fearful",
      description: "Practice expressing concern or fear",
      icon: "😨",
      color: "#a29bfe",
      tips: [
        "Widen your eyes",
        "Raise your eyebrows",
        "Tense your facial muscles slightly",
        "Keep the expression authentic",
      ],
    },
    {
      id: "disgusted",
      name: "Disgusted",
      description: "Practice showing distaste appropriately",
      icon: "🤢",
      color: "#00b894",
      tips: [
        "Wrinkle your nose slightly",
        "Raise your upper lip",
        "Squint your eyes a bit",
        "Keep it subtle and appropriate",
      ],
    },
    {
      id: "neutral",
      name: "Neutral",
      description: "Practice maintaining a calm, neutral expression",
      icon: "😐",
      color: "#636e72",
      tips: [
        "Relax all facial muscles",
        "Keep your mouth in a natural position",
        "Maintain soft, alert eyes",
        "Practice mindful awareness",
      ],
    },
  ];

  // Handle emotion selection
  const handleEmotionSelect = useCallback(emotion => {
    setSelectedEmotion(emotion);
  }, []);

  // Handle starting practice session
  const handleStartPractice = useCallback(async () => {
    if (!selectedEmotion) return;

    setIsStarting(true);
    try {
      await onStartSession(selectedEmotion.id);
    } catch (error) {
      console.error("Error starting practice session:", error);
    } finally {
      setIsStarting(false);
    }
  }, [selectedEmotion, onStartSession]);

  // Handle showing instructions
  const handleShowInstructions = useCallback(() => {
    setShowInstructions(true);
  }, []);

  // Handle closing instructions
  const handleCloseInstructions = useCallback(() => {
    setShowInstructions(false);
  }, []);

  // Check if system is ready for practice - backend connects automatically
  const isSystemReady =
    webcamStatus === "active" || webcamStatus === "inactive";

  return (
    <div className="expression-practice">
      <div className="practice-header">
        <h2>Choose an Emotion to Practice</h2>
        <p>
          Select an emotion below to begin your facial expression practice
          session.
        </p>

        <div className="header-actions">
          <Button
            variant="secondary"
            onClick={handleShowInstructions}
            ariaLabel="Show practice instructions"
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

      {/* Emotion Selection Grid */}
      <div className="emotions-grid">
        {emotions.map(emotion => (
          <div
            key={emotion.id}
            className={`emotion-card ${
              selectedEmotion?.id === emotion.id ? "selected" : ""
            }`}
            onClick={() => handleEmotionSelect(emotion)}
            role="button"
            tabIndex={0}
            aria-pressed={selectedEmotion?.id === emotion.id}
            onKeyDown={e => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleEmotionSelect(emotion);
              }
            }}
          >
            <div
              className="emotion-icon"
              style={{ backgroundColor: emotion.color }}
            >
              {emotion.icon}
            </div>
            <h3>{emotion.name}</h3>
            <p>{emotion.description}</p>

            {selectedEmotion?.id === emotion.id && (
              <div className="emotion-tips">
                <h4>Practice Tips:</h4>
                <ul>
                  {emotion.tips.map((tip, index) => (
                    <li key={index}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Start Practice Button */}
      {selectedEmotion && (
        <div className="start-practice-section">
          <div className="selected-emotion-summary">
            <span
              className="emotion-icon"
              style={{ backgroundColor: selectedEmotion.color }}
            >
              {selectedEmotion.icon}
            </span>
            <div>
              <h3>Ready to practice: {selectedEmotion.name}</h3>
              <p>{selectedEmotion.description}</p>
            </div>
          </div>

          <Button
            variant="primary"
            onClick={handleStartPractice}
            disabled={!isSystemReady || isStarting}
            loading={isStarting}
            ariaLabel={`Start ${selectedEmotion.name} expression practice`}
            className="start-practice-button"
          >
            {isStarting
              ? "Starting Session..."
              : `Start ${selectedEmotion.name} Practice`}
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
        title="Harmony Practice Instructions"
        className="instructions-modal"
      >
        <div className="instructions-content">
          <section>
            <h3>🎯 How It Works</h3>
            <p>
              Harmony uses advanced facial recognition to help you practice
              expressing emotions naturally and appropriately. This builds
              social-emotional learning skills.
            </p>
          </section>

          <section>
            <h3>📋 Getting Started</h3>
            <ol>
              <li>Choose an emotion you'd like to practice</li>
              <li>Read the practice tips for that emotion</li>
              <li>Ensure your camera and connection are ready</li>
              <li>Click "Start Practice" to begin your session</li>
            </ol>
          </section>

          <section>
            <h3>💡 Practice Tips</h3>
            <ul>
              <li>Sit in good lighting facing the camera</li>
              <li>Practice natural, authentic expressions</li>
              <li>Take your time - there's no rush</li>
              <li>Focus on how the emotion feels, not just looks</li>
              <li>Use the real-time feedback to improve</li>
            </ul>
          </section>

          <section>
            <h3>🔒 Privacy & Safety</h3>
            <ul>
              <li>Your video is processed locally when possible</li>
              <li>No video recordings are stored permanently</li>
              <li>Only anonymized progress data is saved</li>
              <li>You can end any session at any time</li>
            </ul>
          </section>
        </div>
      </Modal>
    </div>
  );
};

export default ExpressionPractice;
