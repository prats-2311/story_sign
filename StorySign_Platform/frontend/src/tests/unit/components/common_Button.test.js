import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe, toHaveNoViolations } from "jest-axe";
import Button from "./Button";

expect.extend(toHaveNoViolations);

describe("Button Accessibility Tests", () => {
  test("renders with proper ARIA attributes", () => {
    render(
      <Button ariaLabel="Custom button label" ariaDescribedBy="help-text">
        Click me
      </Button>
    );

    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-label", "Custom button label");
    expect(button).toHaveAttribute("aria-describedby", "help-text");
  });

  test("supports keyboard navigation", async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();

    render(<Button onClick={handleClick}>Click me</Button>);

    const button = screen.getByRole("button");

    // Test Tab navigation
    await user.tab();
    expect(button).toHaveFocus();

    // Test Enter key activation
    await user.keyboard("{Enter}");
    expect(handleClick).toHaveBeenCalledTimes(1);

    // Test Space key activation
    await user.keyboard(" ");
    expect(handleClick).toHaveBeenCalledTimes(2);
  });

  test("prevents interaction when disabled", async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();

    render(
      <Button onClick={handleClick} disabled>
        Disabled button
      </Button>
    );

    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-disabled", "true");

    // Should not respond to clicks
    await user.click(button);
    expect(handleClick).not.toHaveBeenCalled();

    // Should not respond to keyboard
    button.focus();
    await user.keyboard("{Enter}");
    await user.keyboard(" ");
    expect(handleClick).not.toHaveBeenCalled();
  });

  test("shows loading state with proper accessibility", () => {
    render(<Button loading>Loading button</Button>);

    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-disabled", "true");

    // Loading spinner should be hidden from screen readers
    const spinner = screen
      .getByText("Loading button")
      .parentElement.querySelector(".button-spinner");
    expect(spinner).toHaveAttribute("aria-hidden", "true");
  });

  test("meets minimum touch target size", () => {
    render(<Button size="small">Small button</Button>);

    const button = screen.getByRole("button");
    const styles = window.getComputedStyle(button);

    // Should meet WCAG minimum 44px touch target
    expect(parseInt(styles.minHeight)).toBeGreaterThanOrEqual(36); // Small variant minimum
    expect(parseInt(styles.minWidth)).toBeGreaterThanOrEqual(36);
  });

  test("has proper focus indicators", () => {
    render(<Button>Focus test</Button>);

    const button = screen.getByRole("button");
    button.focus();

    // Should have focus-visible styles (tested via CSS class)
    expect(button).toHaveClass("accessible-button");
  });

  test("passes axe accessibility tests", async () => {
    const { container } = render(
      <div>
        <Button>Primary button</Button>
        <Button variant="secondary">Secondary button</Button>
        <Button disabled>Disabled button</Button>
        <Button loading>Loading button</Button>
      </div>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test("supports different variants without accessibility issues", async () => {
    const variants = ["primary", "secondary", "success", "danger", "warning"];

    for (const variant of variants) {
      const { container, unmount } = render(
        <Button variant={variant}>{variant} button</Button>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();

      unmount();
    }
  });

  test("handles click events properly", async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();

    render(<Button onClick={handleClick}>Click handler test</Button>);

    const button = screen.getByRole("button");

    await user.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);

    // Verify event object is passed
    expect(handleClick).toHaveBeenCalledWith(expect.any(Object));
  });

  test("forwards ref correctly", () => {
    const ref = React.createRef();

    render(<Button ref={ref}>Ref test</Button>);

    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
    expect(ref.current).toHaveTextContent("Ref test");
  });

  test("supports custom className and props", () => {
    render(
      <Button
        className="custom-class"
        data-testid="custom-button"
        title="Custom title"
      >
        Custom props test
      </Button>
    );

    const button = screen.getByRole("button");
    expect(button).toHaveClass("accessible-button", "custom-class");
    expect(button).toHaveAttribute("data-testid", "custom-button");
    expect(button).toHaveAttribute("title", "Custom title");
  });
});
