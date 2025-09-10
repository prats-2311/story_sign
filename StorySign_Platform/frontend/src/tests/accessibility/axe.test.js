// Mock API configuration before other imports
jest.mock("../../config/api", () => ({
  getApiConfig: () => ({
    API_BASE_URL: "http://localhost:8000",
    WS_BASE_URL: "ws://localhost:8000",
    API_VERSION: "v1",
  }),
  buildApiUrl: (path) => `http://localhost:8000/api/v1${path}`,
  buildWsUrl: (path) => `ws://localhost:8000${path}`,
  buildHealthCheckUrl: () => "http://localhost:8000/health",
}));

import React from "react";
import { render } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import { MemoryRouter } from "react-router-dom";
import Button from "../../components/common/Button";
import Modal from "../../components/common/Modal";
import SkipLinks from "../../components/common/SkipLinks";
import AccessibleHeading from "../../components/common/AccessibleHeading";
import LiveRegion from "../../components/common/LiveRegion";
import { FormField } from "../../components/common/AccessibleForm";

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Test wrapper component
const TestWrapper = ({ children }) => <MemoryRouter>{children}</MemoryRouter>;

describe("Accessibility Tests with Axe", () => {
  beforeEach(() => {
    expect.extend(toHaveNoViolations);
  });

  describe("Core Application Components", () => {
    test("Simple page structure should not have accessibility violations", async () => {
      const { container } = render(
        <TestWrapper>
          <div>
            <header role="banner">
              <AccessibleHeading level={1}>Test Application</AccessibleHeading>
            </header>
            <main role="main">
              <AccessibleHeading level={2}>Main Content</AccessibleHeading>
              <p>This is a test page for accessibility validation.</p>
            </main>
            <footer role="contentinfo">
              <p>Footer content</p>
            </footer>
          </div>
        </TestWrapper>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe("Interactive Components", () => {
    test("Button component should not have accessibility violations", async () => {
      const { container } = render(
        <TestWrapper>
          <Button>Test Button</Button>
        </TestWrapper>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    test("Modal component should not have accessibility violations", async () => {
      const { container } = render(
        <TestWrapper>
          <Modal isOpen={true} onClose={jest.fn()} title="Test Modal">
            <p>Modal content</p>
          </Modal>
        </TestWrapper>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    test("Form components should not have accessibility violations", async () => {
      const { container } = render(
        <TestWrapper>
          <form>
            <FormField
              id="test-input"
              label="Test Input"
              type="text"
              value=""
              onChange={jest.fn()}
            />
          </form>
        </TestWrapper>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe("Navigation Components", () => {
    test("Skip links should not have accessibility violations", async () => {
      const { container } = render(
        <TestWrapper>
          <SkipLinks />
        </TestWrapper>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe("Live Regions", () => {
    test("Live region should not have accessibility violations", async () => {
      const { container } = render(
        <TestWrapper>
          <LiveRegion message="Test announcement" politeness="polite" />
        </TestWrapper>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe("Dynamic Content", () => {
    test("should handle dynamic content accessibility", async () => {
      const DynamicComponent = () => {
        const [showModal, setShowModal] = React.useState(false);

        return (
          <div>
            <Button onClick={() => setShowModal(true)}>Open Modal</Button>
            {showModal && (
              <Modal
                isOpen={showModal}
                onClose={() => setShowModal(false)}
                title="Test Modal"
              >
                <p>This is a test modal for accessibility testing.</p>
              </Modal>
            )}
          </div>
        );
      };

      const { container } = render(
        <TestWrapper>
          <DynamicComponent />
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});
