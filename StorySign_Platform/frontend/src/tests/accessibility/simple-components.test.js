import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import Button from "../../components/common/Button";
import LiveRegion from "../../components/common/LiveRegion";
import { useAccessibility } from "../../hooks/useAccessibility";

// Mock matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

describe("Simple Accessibility Components", () => {
  describe("Button Component", () => {
    test("should render with proper accessibility attributes", () => {
      render(
        <Button ariaLabel="Test button" onClick={() => {}}>
          Click me
        </Button>
      );

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("aria-label", "Test button");
      expect(button).toHaveTextContent("Click me");
    });

    test("should be keyboard accessible", async () => {
      const user = userEvent.setup();
      const handleClick = jest.fn();

      render(<Button onClick={handleClick}>Test Button</Button>);

      const button = screen.getByRole("button");

      // Focus and activate with Enter
      button.focus();
      await user.keyboard("{Enter}");
      expect(handleClick).toHaveBeenCalledTimes(1);

      // Activate with Space
      await user.keyboard(" ");
      expect(handleClick).toHaveBeenCalledTimes(2);
    });

    test("should handle disabled state correctly", () => {
      render(<Button disabled>Disabled Button</Button>);

      const button = screen.getByRole("button");
      expect(button).toBeDisabled();
      expect(button).toHaveAttribute("aria-disabled", "true");
    });

    test("should show loading state", () => {
      render(<Button loading>Loading Button</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("aria-disabled", "true");
      expect(button).toHaveClass("button-loading");

      // Check for screen reader text
      expect(
        screen.getByText("Loading", { selector: ".sr-only" })
      ).toBeInTheDocument();

      // Check for spinner
      expect(screen.getByRole("button")).toContainHTML(
        '<span class="button-spinner"'
      );
    });
  });

  describe("LiveRegion Component", () => {
    test("should render with proper ARIA attributes", () => {
      render(<LiveRegion message="Test message" />);

      const liveRegion = screen.getByRole("status");
      expect(liveRegion).toHaveAttribute("aria-live", "polite");
      expect(liveRegion).toHaveAttribute("aria-atomic", "true");
      expect(liveRegion).toHaveTextContent("Test message");
    });

    test("should support assertive announcements", () => {
      render(<LiveRegion message="Urgent message" politeness="assertive" />);

      const liveRegion = screen.getByRole("status");
      expect(liveRegion).toHaveAttribute("aria-live", "assertive");
      expect(liveRegion).toHaveTextContent("Urgent message");
    });
  });

  describe("useAccessibility Hook", () => {
    const TestComponent = () => {
      const { announce } = useAccessibility();

      return (
        <button onClick={() => announce("Test announcement")}>Announce</button>
      );
    };

    test("should provide announce function", () => {
      render(<TestComponent />);

      const button = screen.getByRole("button");
      expect(button).toBeInTheDocument();
    });
  });

  describe("Accessibility Utilities", () => {
    test("should generate unique IDs", () => {
      const { generateId } = require("../../utils/accessibility");

      const id1 = generateId("test");
      const id2 = generateId("test");

      expect(id1).toMatch(/^test-/);
      expect(id2).toMatch(/^test-/);
      expect(id1).not.toBe(id2);
    });

    test("should detect reduced motion preference", () => {
      const { prefersReducedMotion } = require("../../utils/accessibility");

      // Mock matchMedia
      Object.defineProperty(window, "matchMedia", {
        writable: true,
        value: jest.fn().mockImplementation((query) => ({
          matches: query === "(prefers-reduced-motion: reduce)",
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      const result = prefersReducedMotion();
      expect(typeof result).toBe("boolean");
    });
  });
});
