import React from "react";
import { Button } from "../../components/common";
import "./StorySelection.css";

/**
 * StorySelection component for choosing difficulty levels
 * Displays available stories with difficulty information and previews
 */
const StorySelection = ({ storyData, onStorySelect, onBackToGeneration }) => {
  if (!storyData) {
    return (
      <div className="story-selection-error" role="alert">
        <h3>No Stories Available</h3>
        <p>Please generate stories first to see selection options.</p>
      </div>
    );
  }

  const difficulties = [
    {
      key: "amateur",
      title: "Amateur",
      description: "Simple words and basic sentence structure",
      recommended: false,
    },
    {
      key: "normal",
      title: "Normal",
      description: "Slightly more complex vocabulary",
      recommended: false,
    },
    {
      key: "mid_level",
      title: "Mid-Level",
      description: "Introduces classifiers and rhetorical questions",
      recommended: true,
    },
    {
      key: "difficult",
      title: "Difficult",
      description: "Complex grammar and varied structures",
      recommended: false,
    },
    {
      key: "expert",
      title: "Expert",
      description: "Advanced concepts and facial expressions",
      recommended: false,
    },
  ];

  const getDifficultyColor = (key) => {
    const colors = {
      amateur: "#16a34a",
      normal: "#2563eb",
      mid_level: "#7c3aed",
      difficult: "#dc2626",
      expert: "#991b1b",
    };
    return colors[key] || "#6b7280";
  };

  return (
    <div className="story-selection">
      <header className="selection-header">
        <h2>Choose Your Challenge Level</h2>
        <p>Select the difficulty level that matches your ASL skills.</p>
      </header>

      <main
        className="difficulty-grid"
        role="group"
        aria-label="Story difficulty levels"
      >
        {difficulties.map((difficulty) => {
          const story = storyData[difficulty.key];
          if (!story) return null;

          return (
            <article
              key={difficulty.key}
              className={`difficulty-card ${
                difficulty.recommended ? "recommended" : ""
              }`}
              style={{
                "--difficulty-color": getDifficultyColor(difficulty.key),
              }}
            >
              <header className="card-header">
                <h3>
                  {difficulty.title}
                  {difficulty.recommended && (
                    <span
                      className="recommended-badge"
                      aria-label="Recommended difficulty"
                    >
                      Recommended
                    </span>
                  )}
                </h3>
                <div className="difficulty-info">
                  <span
                    className="sentence-count"
                    aria-label={`${story.sentences.length} sentences`}
                  >
                    {story.sentences.length} sentences
                  </span>
                </div>
              </header>

              <div className="card-content">
                <p className="difficulty-description">
                  {difficulty.description}
                </p>

                <div className="story-preview">
                  <h4 className="story-title">"{story.title}"</h4>
                  <blockquote className="first-sentence">
                    "{story.sentences[0]}"
                  </blockquote>

                  {story.sentences.length > 1 && (
                    <details className="more-sentences">
                      <summary>
                        View all {story.sentences.length} sentences
                      </summary>
                      <ol className="sentence-list">
                        {story.sentences.map((sentence, index) => (
                          <li key={index} className="sentence-item">
                            {sentence}
                          </li>
                        ))}
                      </ol>
                    </details>
                  )}
                </div>
              </div>

              <footer className="card-footer">
                <Button
                  variant="primary"
                  size="large"
                  onClick={() => onStorySelect(story)}
                  ariaLabel={`Select ${difficulty.title} difficulty story: ${story.title}`}
                  className="select-story-button"
                >
                  Select This Story
                </Button>
              </footer>
            </article>
          );
        })}
      </main>

      <footer className="selection-footer">
        <Button
          variant="secondary"
          onClick={onBackToGeneration}
          ariaLabel="Go back to story generation"
        >
          ← Generate Different Stories
        </Button>
      </footer>
    </div>
  );
};

export default StorySelection;
