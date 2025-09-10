import React from "react";
import { render, screen } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import LoadingSpinner, {
  InlineSpinner,
  PageLoader,
  ContentLoader,
} from "./LoadingSpinner";

expect.extend(toHaveNoViolations);

describe("LoadingSpinner Accessibility Tests", () => {
  test("renders with proper ARIA attributes", () => {
    render(<LoadingSpinner message="Loading content" />);

    const spinner = screen.getByRole("status");
    expect(spinner).toHaveAttribute("aria-label", "Loading content");
    expect(spinner).toHaveAttribute("aria-live", "polite");
  });

  test("provides screen reader text", () => {
    render(<LoadingSpinner message="Loading data" />);

    // Should have visible message
    expect(screen.getByText("Loading data")).toBeInTheDocument();

    // Should have screen reader only text
    const srText = document.querySelector(".sr-only");
    expect(srText).toHaveTextContent("Loading data");
  });

  test("supports custom aria-label", () => {
    render(
      <LoadingSpinner message="Loading..." ariaLabel="Custom loading message" />
    );

    const spinner = screen.getByRole("status");
    expect(spinner).toHaveAttribute("aria-label", "Custom loading message");
  });

  test("hides spinner animation from screen readers", () => {
    render(<LoadingSpinner />);

    const spinnerCircle = document.querySelector(".spinner-circle");
    expect(spinnerCircle).toHaveAttribute("aria-hidden", "true");
  });

  test("supports different sizes", () => {
    const sizes = ["small", "medium", "large", "extra-large"];

    sizes.forEach((size) => {
      const { unmount } = render(<LoadingSpinner size={size} />);

      const spinner = screen.getByRole("status");
      expect(spinner).toHaveClass(`spinner-${size}`);

      unmount();
    });
  });

  test("supports different variants", () => {
    const variants = ["primary", "secondary", "success", "warning", "danger"];

    variants.forEach((variant) => {
      const { unmount } = render(<LoadingSpinner variant={variant} />);

      const spinner = screen.getByRole("status");
      expect(spinner).toHaveClass(`spinner-${variant}`);

      unmount();
    });
  });

  test("can hide message text", () => {
    render(<LoadingSpinner message="Hidden message" showMessage={false} />);

    expect(screen.queryByText("Hidden message")).not.toBeInTheDocument();

    // Should still have screen reader text
    const srText = document.querySelector(".sr-only");
    expect(srText).toHaveTextContent("Hidden message");
  });

  test("inline variant renders correctly", () => {
    render(<LoadingSpinner inline={true} message="Inline loading" />);

    const spinner = screen.getByRole("status");
    expect(spinner).toHaveClass("spinner-inline");

    const container = spinner.closest(".loading-spinner-container");
    expect(container).toHaveClass("container-inline");
  });

  test("passes axe accessibility tests", async () => {
    const { container } = render(
      <div>
        <LoadingSpinner message="Default spinner" />
        <LoadingSpinner
          size="large"
          variant="success"
          message="Large success spinner"
        />
        <LoadingSpinner inline={true} message="Inline spinner" />
      </div>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  describe("InlineSpinner", () => {
    test("renders as inline variant", () => {
      render(<InlineSpinner ariaLabel="Inline loading" />);

      const spinner = screen.getByRole("status");
      expect(spinner).toHaveClass("spinner-inline");
      expect(spinner).toHaveAttribute("aria-label", "Inline loading");
    });

    test("has no visible message by default", () => {
      render(<InlineSpinner />);

      expect(screen.queryByText("Loading")).not.toBeInTheDocument();
    });
  });

  describe("PageLoader", () => {
    test("renders with overlay", () => {
      render(<PageLoader message="Loading page" />);

      const overlay = document.querySelector(".page-loader-overlay");
      expect(overlay).toBeInTheDocument();

      expect(screen.getByText("Loading page")).toBeInTheDocument();
    });

    test("passes axe accessibility tests", async () => {
      const { container } = render(<PageLoader />);

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe("ContentLoader", () => {
    test("renders in content container", () => {
      render(<ContentLoader message="Loading content" />);

      const container = document.querySelector(".content-loader-container");
      expect(container).toBeInTheDocument();

      expect(screen.getByText("Loading content")).toBeInTheDocument();
    });

    test("passes axe accessibility tests", async () => {
      const { container } = render(<ContentLoader />);

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  test("supports custom className", () => {
    render(<LoadingSpinner className="custom-spinner" />);

    const spinner = screen.getByRole("status");
    expect(spinner).toHaveClass("loading-spinner", "custom-spinner");
  });

  test("handles reduced motion preference", () => {
    // Mock reduced motion preference
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

    render(<LoadingSpinner />);

    const spinner = screen.getByRole("status");
    expect(spinner).toBeInTheDocument();

    // Should still be accessible even with reduced motion
    expect(spinner).toHaveAttribute("aria-live", "polite");
  });

  test("maintains accessibility with different color variants", async () => {
    const variants = [
      "primary",
      "secondary",
      "success",
      "warning",
      "danger",
      "inherit",
      "white",
    ];

    for (const variant of variants) {
      const { container, unmount } = render(
        <LoadingSpinner variant={variant} message={`${variant} spinner`} />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();

      unmount();
    }
  });

  test("provides appropriate role and live region", () => {
    render(<LoadingSpinner message="Testing roles" />);

    const spinner = screen.getByRole("status");
    expect(spinner).toHaveAttribute("role", "status");
    expect(spinner).toHaveAttribute("aria-live", "polite");
  });
});
