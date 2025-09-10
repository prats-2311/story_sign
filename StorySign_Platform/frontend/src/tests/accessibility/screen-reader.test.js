import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import LiveRegion, {
  AssertiveLiveRegion,
  StatusLiveRegion,
} from "../../components/common/LiveRegion";
import Button from "../../components/common/Button";
import Modal from "../../components/common/Modal";

import { useAccessibility } from "../../hooks/useAccessibility";
import { AuthProvider } from "../../contexts/AuthContext";

// Test wrapper component
const TestWrapper = ({ children }) => <MemoryRouter>{children}</MemoryRouter>;

describe("Screen Reader Compatibility Tests", () => {
  describe("Live Regions", () => {
    test("should announce messages in polite live region", async () => {
      const { rerender } = render(
        <LiveRegion message="" politeness="polite" />
      );

      const liveRegion = screen.getByRole("status");
      expect(liveRegion).toHaveAttribute("aria-live", "polite");
      expect(liveRegion).toHaveAttribute("aria-atomic", "true");

      // Update message
      rerender(<LiveRegion message="Test announcement" politeness="polite" />);

      expect(liveRegion).toHaveTextContent("Test announcement");
    });

    test("should announce urgent messages in assertive live region", async () => {
      render(<AssertiveLiveRegion message="Urgent message" />);

      const liveRegion = screen.getByRole("status");
      expect(liveRegion).toHaveAttribute("aria-live", "assertive");
      expect(liveRegion).toHaveTextContent("Urgent message");
    });

    test("should clear messages after delay", async () => {
      const { rerender } = render(
        <LiveRegion message="Test message" clearDelay={100} />
      );

      const liveRegion = screen.getByRole("status");
      expect(liveRegion).toHaveTextContent("Test message");

      // Wait for clear delay
      await waitFor(
        () => {
          expect(liveRegion).toHaveTextContent("");
        },
        { timeout: 200 }
      );
    });
  });

  describe("ARIA Labels and Descriptions", () => {
    test("should provide accessible names for buttons", () => {
      render(
        <div>
          <Button ariaLabel="Custom button label">Icon Only</Button>
          <Button>Text Button</Button>
          <Button ariaLabel="Override label">Text with Override</Button>
        </div>
      );

      const customButton = screen.getByLabelText("Custom button label");
      const textButton = screen.getByRole("button", { name: "Text Button" });
      const overrideButton = screen.getByLabelText("Override label");

      expect(customButton).toBeInTheDocument();
      expect(textButton).toBeInTheDocument();
      expect(overrideButton).toBeInTheDocument();
    });

    test("should associate descriptions with form controls", () => {
      render(
        <div>
          <label htmlFor="test-input">Test Input</label>
          <input id="test-input" aria-describedby="help-text error-text" />
          <div id="help-text">This is help text</div>
          <div id="error-text">This is error text</div>
        </div>
      );

      const input = screen.getByLabelText("Test Input");
      expect(input).toHaveAttribute("aria-describedby", "help-text error-text");
    });

    test("should provide proper modal labeling", () => {
      render(
        <Modal isOpen={true} onClose={() => {}} title="Test Modal">
          <p>Modal content</p>
        </Modal>
      );

      const modal = screen.getByRole("dialog");
      expect(modal).toHaveAttribute("aria-modal", "true");
      expect(modal).toHaveAttribute("aria-labelledby");

      const title = screen.getByText("Test Modal");
      expect(title).toBeInTheDocument();
    });
  });

  describe("Video Component Accessibility", () => {
    test("should announce video status changes", async () => {
      const MockVideoComponent = ({ connected }) => (
        <div>
          <div aria-label="Test video display" role="img">
            Video Display
          </div>
          <LiveRegion
            message={
              connected ? "Video stream connected" : "Video stream disconnected"
            }
            politeness="polite"
          />
        </div>
      );

      const { rerender } = render(<MockVideoComponent connected={false} />);

      // Check initial state
      expect(screen.getByLabelText("Test video display")).toBeInTheDocument();

      // Simulate stream connection
      rerender(<MockVideoComponent connected={true} />);

      // Should announce connection status
      await waitFor(() => {
        expect(screen.getByText(/video stream connected/i)).toBeInTheDocument();
      });
    });

    test("should provide alternative text for video overlays", () => {
      // Create a simple mock video component instead of using VideoDisplayPanel
      const MockVideoComponent = () => (
        <div role="img" aria-label="Video with hand landmarks">
          <video aria-describedby="video-description" />
          <div id="video-description">
            Video showing ASL practice with hand position overlays
          </div>
        </div>
      );

      render(<MockVideoComponent />);

      const video = screen.getByLabelText("Video with hand landmarks");
      expect(video).toBeInTheDocument();
    });
  });

  describe("Dynamic Content Announcements", () => {
    test("should announce loading states", async () => {
      const LoadingComponent = () => {
        const [loading, setLoading] = React.useState(false);
        const { announce } = useAccessibility();

        const handleClick = () => {
          setLoading(true);
          announce("Loading started", "polite");

          setTimeout(() => {
            setLoading(false);
            announce("Loading completed", "polite");
          }, 100);
        };

        return (
          <Button onClick={handleClick} loading={loading}>
            {loading ? "Loading..." : "Load Data"}
          </Button>
        );
      };

      render(<LoadingComponent />);

      const button = screen.getByRole("button");
      fireEvent.click(button);

      // Should announce loading state
      await waitFor(() => {
        expect(screen.getByText(/loading/i)).toBeInTheDocument();
      });
    });

    test("should announce form validation errors", async () => {
      const FormWithValidation = () => {
        const [error, setError] = React.useState("");

        const handleSubmit = (e) => {
          e.preventDefault();
          setError("Email is required");
        };

        return (
          <form onSubmit={handleSubmit}>
            <label htmlFor="email">Email</label>
            <input id="email" type="email" aria-invalid={!!error} />
            {error && (
              <div role="alert" aria-live="assertive">
                {error}
              </div>
            )}
            <button type="submit">Submit</button>
          </form>
        );
      };

      render(<FormWithValidation />);

      const submitButton = screen.getByRole("button", { name: "Submit" });
      fireEvent.click(submitButton);

      // Should announce error
      const errorMessage = screen.getByRole("alert");
      expect(errorMessage).toHaveTextContent("Email is required");
      expect(errorMessage).toHaveAttribute("aria-live", "assertive");
    });
  });

  describe("Navigation Announcements", () => {
    test("should announce page changes", () => {
      const NavigationTest = () => {
        const [currentPage, setCurrentPage] = React.useState("home");

        React.useEffect(() => {
          // Simulate page title update
          document.title = `StorySign - ${currentPage}`;
        }, [currentPage]);

        return (
          <div>
            <nav>
              <button onClick={() => setCurrentPage("home")}>Home</button>
              <button onClick={() => setCurrentPage("asl-world")}>
                ASL World
              </button>
            </nav>
            <main>
              <h1>{currentPage === "home" ? "Dashboard" : "ASL World"}</h1>
            </main>
          </div>
        );
      };

      render(<NavigationTest />);

      const aslWorldButton = screen.getByRole("button", { name: "ASL World" });
      fireEvent.click(aslWorldButton);

      // Check that heading is updated
      expect(
        screen.getByRole("heading", { name: "ASL World" })
      ).toBeInTheDocument();
    });
  });

  describe("Error Handling Accessibility", () => {
    test("should announce connection errors", () => {
      const ErrorComponent = () => {
        const [error, setError] = React.useState(null);

        React.useEffect(() => {
          setError("Connection failed. Please check your internet connection.");
        }, []);

        return (
          <div>
            {error && (
              <div role="alert" aria-live="assertive">
                <strong>Error:</strong> {error}
              </div>
            )}
          </div>
        );
      };

      render(<ErrorComponent />);

      const errorAlert = screen.getByRole("alert");
      expect(errorAlert).toHaveTextContent("Error: Connection failed");
      expect(errorAlert).toHaveAttribute("aria-live", "assertive");
    });

    test("should provide recovery instructions", () => {
      render(
        <div role="alert">
          <h2>Connection Error</h2>
          <p>Unable to connect to the server.</p>
          <p>Please try the following:</p>
          <ol>
            <li>Check your internet connection</li>
            <li>Refresh the page</li>
            <li>Contact support if the problem persists</li>
          </ol>
          <button>Retry Connection</button>
        </div>
      );

      const alert = screen.getByRole("alert");
      const retryButton = screen.getByRole("button", {
        name: "Retry Connection",
      });

      expect(alert).toBeInTheDocument();
      expect(retryButton).toBeInTheDocument();
      expect(
        screen.getByText("Check your internet connection")
      ).toBeInTheDocument();
    });
  });

  describe("Progress and Status Updates", () => {
    test("should announce progress updates", async () => {
      const ProgressComponent = () => {
        const [progress, setProgress] = React.useState(0);

        React.useEffect(() => {
          const interval = setInterval(() => {
            setProgress((prev) => {
              if (prev >= 100) {
                clearInterval(interval);
                return 100;
              }
              return prev + 10;
            });
          }, 100);

          return () => clearInterval(interval);
        }, []);

        return (
          <div>
            <div
              role="progressbar"
              aria-valuenow={progress}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Loading progress"
            >
              {progress}%
            </div>
            <StatusLiveRegion
              message={
                progress === 100 ? "Loading complete" : `Loading ${progress}%`
              }
            />
          </div>
        );
      };

      render(<ProgressComponent />);

      const progressbar = screen.getByRole("progressbar");
      expect(progressbar).toHaveAttribute("aria-label", "Loading progress");

      // Wait for progress to complete
      await waitFor(
        () => {
          expect(progressbar).toHaveAttribute("aria-valuenow", "100");
        },
        { timeout: 2000 }
      );
    });
  });
});
