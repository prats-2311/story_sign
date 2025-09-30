import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe, toHaveNoViolations } from "jest-axe";
import Modal from "./Modal";

expect.extend(toHaveNoViolations);

describe("Modal Accessibility Tests", () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    title: "Test Modal",
    children: <div>Modal content</div>,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders with proper ARIA attributes", () => {
    render(<Modal {...defaultProps} ariaDescribedBy="modal-description" />);

    const modal = screen.getByRole("dialog");
    expect(modal).toHaveAttribute("aria-modal", "true");
    expect(modal).toHaveAttribute("aria-labelledby");
    expect(modal).toHaveAttribute("aria-describedby", "modal-description");

    const title = screen.getByRole("heading", { level: 2 });
    expect(title).toHaveTextContent("Test Modal");
  });

  test("traps focus within modal", async () => {
    const user = userEvent.setup();

    render(
      <div>
        <button>Outside button</button>
        <Modal {...defaultProps}>
          <button>First button</button>
          <button>Second button</button>
        </Modal>
      </div>
    );

    const firstButton = screen.getByText("First button");
    const secondButton = screen.getByText("Second button");
    const closeButton = screen.getByLabelText("Close modal");

    // Focus should be trapped within modal
    await user.tab();
    expect(firstButton).toHaveFocus();

    await user.tab();
    expect(secondButton).toHaveFocus();

    await user.tab();
    expect(closeButton).toHaveFocus();

    // Should cycle back to first focusable element
    await user.tab();
    expect(firstButton).toHaveFocus();

    // Test reverse tab order
    await user.tab({ shift: true });
    expect(closeButton).toHaveFocus();
  });

  test("closes on Escape key", async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();

    render(<Modal {...defaultProps} onClose={onClose} />);

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  test("prevents Escape close when disabled", async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();

    render(<Modal {...defaultProps} onClose={onClose} closeOnEscape={false} />);

    await user.keyboard("{Escape}");
    expect(onClose).not.toHaveBeenCalled();
  });

  test("closes on overlay click when enabled", async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();

    render(<Modal {...defaultProps} onClose={onClose} />);

    const overlay = screen.getByRole("presentation");
    await user.click(overlay);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  test("prevents overlay close when disabled", async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();

    render(
      <Modal {...defaultProps} onClose={onClose} closeOnOverlayClick={false} />
    );

    const overlay = screen.getByRole("presentation");
    await user.click(overlay);
    expect(onClose).not.toHaveBeenCalled();
  });

  test("focuses initial element when specified", async () => {
    const initialFocusRef = React.createRef();

    render(
      <Modal {...defaultProps} initialFocusRef={initialFocusRef}>
        <button>First button</button>
        <button ref={initialFocusRef}>Focus me first</button>
      </Modal>
    );

    await waitFor(() => {
      expect(initialFocusRef.current).toHaveFocus();
    });
  });

  test("restores focus to previous element on close", async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();

    const { rerender } = render(
      <div>
        <button>Trigger button</button>
        <Modal isOpen={false} onClose={onClose} title="Test">
          Content
        </Modal>
      </div>
    );

    const triggerButton = screen.getByText("Trigger button");
    triggerButton.focus();
    expect(triggerButton).toHaveFocus();

    // Open modal
    rerender(
      <div>
        <button>Trigger button</button>
        <Modal isOpen={true} onClose={onClose} title="Test">
          <button>Modal button</button>
        </Modal>
      </div>
    );

    // Close modal
    rerender(
      <div>
        <button>Trigger button</button>
        <Modal isOpen={false} onClose={onClose} title="Test">
          Content
        </Modal>
      </div>
    );

    await waitFor(() => {
      expect(triggerButton).toHaveFocus();
    });
  });

  test("prevents body scroll when open", () => {
    const { rerender } = render(<Modal {...defaultProps} isOpen={false} />);

    expect(document.body.style.overflow).toBe("");

    rerender(<Modal {...defaultProps} isOpen={true} />);
    expect(document.body.style.overflow).toBe("hidden");

    rerender(<Modal {...defaultProps} isOpen={false} />);
    expect(document.body.style.overflow).toBe("");
  });

  test("renders in portal to avoid z-index issues", () => {
    render(<Modal {...defaultProps} />);

    // Modal should be rendered directly in document.body
    const modal = screen.getByRole("dialog");
    expect(modal.closest("body")).toBeTruthy();
  });

  test("supports different sizes", () => {
    const sizes = ["small", "medium", "large", "full"];

    sizes.forEach((size) => {
      const { unmount } = render(<Modal {...defaultProps} size={size} />);

      const modal = screen.getByRole("dialog");
      expect(modal).toHaveClass(`modal-${size}`);

      unmount();
    });
  });

  test("passes axe accessibility tests", async () => {
    const { container } = render(<Modal {...defaultProps} />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test("handles close button click", async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();

    render(<Modal {...defaultProps} onClose={onClose} />);

    const closeButton = screen.getByLabelText("Close modal");
    await user.click(closeButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  test("hides close button when disabled", () => {
    render(<Modal {...defaultProps} showCloseButton={false} />);

    expect(screen.queryByLabelText("Close modal")).not.toBeInTheDocument();
  });

  test("does not render when closed", () => {
    render(<Modal {...defaultProps} isOpen={false} />);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  test("supports custom className", () => {
    render(<Modal {...defaultProps} className="custom-modal" />);

    const modal = screen.getByRole("dialog");
    expect(modal).toHaveClass("modal-content", "custom-modal");
  });

  test("handles complex content with multiple focusable elements", async () => {
    const user = userEvent.setup();

    render(
      <Modal {...defaultProps}>
        <input type="text" placeholder="Text input" />
        <select>
          <option>Option 1</option>
        </select>
        <textarea placeholder="Textarea"></textarea>
        <a href="#test">Link</a>
        <button tabIndex={0}>Focusable button</button>
        <div tabIndex={-1}>Non-focusable div</div>
      </Modal>
    );

    // Should focus first focusable element
    const textInput = screen.getByPlaceholderText("Text input");
    await waitFor(() => {
      expect(textInput).toHaveFocus();
    });

    // Tab through all focusable elements
    await user.tab(); // select
    await user.tab(); // textarea
    await user.tab(); // link
    await user.tab(); // button
    await user.tab(); // close button
    await user.tab(); // should cycle back to text input

    expect(textInput).toHaveFocus();
  });
});
