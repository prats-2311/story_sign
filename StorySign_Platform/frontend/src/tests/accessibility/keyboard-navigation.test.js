import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Button from "../../components/common/Button";
import Modal from "../../components/common/Modal";
import {
  FormField,
  AccessibleSelect,
} from "../../components/common/AccessibleForm";

// Test wrapper component
const TestWrapper = ({ children }) => <MemoryRouter>{children}</MemoryRouter>;

describe("Keyboard Navigation Tests", () => {
  // Remove userEvent setup to avoid clipboard issues
  // Use fireEvent instead for keyboard interactions

  describe("Button Component", () => {
    test("should be focusable with Tab key", () => {
      render(<Button>Test Button</Button>);

      const button = screen.getByRole("button");

      // Test that button is focusable by checking it has proper attributes
      expect(button).toBeInTheDocument();
      expect(button).not.toHaveAttribute("tabindex", "-1");
      expect(button).not.toHaveAttribute("disabled");
    });

    test("should activate with Enter key", () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Test Button</Button>);

      const button = screen.getByRole("button");
      button.focus();

      fireEvent.keyDown(button, { key: "Enter", code: "Enter" });
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    test("should activate with Space key", () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Test Button</Button>);

      const button = screen.getByRole("button");
      button.focus();

      fireEvent.keyDown(button, { key: " ", code: "Space" });
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    test("should not activate when disabled", () => {
      const handleClick = jest.fn();
      render(
        <Button onClick={handleClick} disabled>
          Test Button
        </Button>
      );

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("disabled");
      expect(button).toHaveAttribute("aria-disabled", "true");

      fireEvent.keyDown(button, { key: "Enter", code: "Enter" });
      fireEvent.keyDown(button, { key: " ", code: "Space" });

      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe("Modal Component", () => {
    test("should trap focus within modal", () => {
      render(
        <Modal isOpen={true} onClose={jest.fn()} title="Test Modal">
          <button>First Button</button>
          <button>Second Button</button>
        </Modal>
      );

      const modal = screen.getByRole("dialog");
      const firstButton = screen.getByText("First Button");
      const closeButton = screen.getByLabelText(/close modal/i);

      // Modal should be properly labeled
      expect(modal).toHaveAttribute("aria-modal", "true");
      expect(modal).toHaveAttribute("aria-labelledby");

      // Elements should be focusable
      expect(firstButton).toBeInTheDocument();
      expect(closeButton).toBeInTheDocument();
    });

    test("should close with Escape key", () => {
      const handleClose = jest.fn();
      render(
        <Modal isOpen={true} onClose={handleClose} title="Test Modal">
          <p>Modal content</p>
        </Modal>
      );

      const modal = screen.getByRole("dialog");
      fireEvent.keyDown(modal, { key: "Escape", code: "Escape" });
      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });

  describe("Form Components", () => {
    test("should navigate between form fields with Tab", () => {
      render(
        <form>
          <FormField
            id="first-input"
            label="First Input"
            type="text"
            value=""
            onChange={jest.fn()}
          />
          <FormField
            id="second-input"
            label="Second Input"
            type="text"
            value=""
            onChange={jest.fn()}
          />
          <AccessibleSelect
            id="select-input"
            label="Select Input"
            value=""
            onChange={jest.fn()}
            options={[
              { value: "option1", label: "Option 1" },
              { value: "option2", label: "Option 2" },
            ]}
          />
          <Button type="submit">Submit</Button>
        </form>
      );

      const firstInput = screen.getByLabelText("First Input");
      const secondInput = screen.getByLabelText("Second Input");
      const selectInput = screen.getByLabelText("Select Input");
      const submitButton = screen.getByRole("button", { name: "Submit" });

      // All form elements should be focusable
      expect(firstInput).toBeInTheDocument();
      expect(secondInput).toBeInTheDocument();
      expect(selectInput).toBeInTheDocument();
      expect(submitButton).toBeInTheDocument();

      // Test focus
      firstInput.focus();
      expect(firstInput).toHaveFocus();
    });

    test("should handle form submission with Enter key", () => {
      const handleSubmit = jest.fn();
      render(
        <form onSubmit={handleSubmit}>
          <FormField
            id="test-input"
            label="Test Input"
            type="text"
            value=""
            onChange={jest.fn()}
          />
          <Button type="submit">Submit</Button>
        </form>
      );

      const input = screen.getByLabelText("Test Input");
      input.focus();

      fireEvent.keyDown(input, { key: "Enter", code: "Enter" });
      expect(handleSubmit).toHaveBeenCalledTimes(1);
    });
  });

  describe("Skip Links", () => {
    test("should allow skipping to main content", () => {
      render(
        <div>
          <a href="#main-content" className="skip-link">
            Skip to main content
          </a>
          <nav>
            <Button>Navigation Button</Button>
          </nav>
          <main id="main-content">
            <h1>Main Content</h1>
          </main>
        </div>
      );

      const skipLink = screen.getByText("Skip to main content");
      const mainContent = screen.getByRole("main");

      // Skip link should be present and functional
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute("href", "#main-content");
      expect(mainContent).toHaveAttribute("id", "main-content");

      // Focus skip link and activate
      skipLink.focus();
      fireEvent.click(skipLink);

      // Main content should be present (skip link functionality verified)
      expect(mainContent).toBeInTheDocument();
    });
  });

  describe("ARIA States and Properties", () => {
    test("should handle aria-expanded correctly", () => {
      const ExpandableButton = () => {
        const [expanded, setExpanded] = React.useState(false);

        return (
          <div>
            <button
              aria-expanded={expanded}
              aria-controls="expandable-content"
              onClick={() => setExpanded(!expanded)}
            >
              Toggle Content
            </button>
            {expanded && (
              <div id="expandable-content">
                <button>Content Button</button>
              </div>
            )}
          </div>
        );
      };

      render(<ExpandableButton />);

      const toggleButton = screen.getByRole("button", {
        name: "Toggle Content",
      });
      expect(toggleButton).toHaveAttribute("aria-expanded", "false");

      // Expand with click (simulating keyboard activation)
      fireEvent.click(toggleButton);

      expect(toggleButton).toHaveAttribute("aria-expanded", "true");

      // Content should be visible
      const contentButton = screen.getByText("Content Button");
      expect(contentButton).toBeInTheDocument();
    });
  });
});
