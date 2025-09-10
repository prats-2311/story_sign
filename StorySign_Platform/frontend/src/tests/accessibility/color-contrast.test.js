import {
  getContrastRatio,
  meetsContrastRequirement,
} from "../../utils/accessibility";

describe("Color Contrast Tests", () => {
  describe("Contrast Ratio Calculation", () => {
    test("should calculate correct contrast ratios", () => {
      // Black on white (maximum contrast)
      expect(getContrastRatio("#000000", "#ffffff")).toBeCloseTo(21, 1);

      // White on black (same ratio, reversed)
      expect(getContrastRatio("#ffffff", "#000000")).toBeCloseTo(21, 1);

      // Same colors (minimum contrast)
      expect(getContrastRatio("#ffffff", "#ffffff")).toBeCloseTo(1, 1);
      expect(getContrastRatio("#000000", "#000000")).toBeCloseTo(1, 1);

      // Common UI colors
      expect(getContrastRatio("#2563eb", "#ffffff")).toBeGreaterThan(4.5); // Blue on white
      expect(getContrastRatio("#dc2626", "#ffffff")).toBeGreaterThan(4.5); // Red on white
      expect(getContrastRatio("#047857", "#ffffff")).toBeGreaterThan(4.5); // Darker green on white
    });

    test("should handle RGB color format", () => {
      const ratio1 = getContrastRatio("rgb(0, 0, 0)", "rgb(255, 255, 255)");
      const ratio2 = getContrastRatio("#000000", "#ffffff");

      expect(ratio1).toBeCloseTo(ratio2, 1);
    });
  });

  describe("WCAG Compliance", () => {
    test("should validate AA compliance for normal text", () => {
      // These should pass AA (4.5:1 minimum)
      expect(
        meetsContrastRequirement("#000000", "#ffffff", "AA", "normal")
      ).toBe(true);
      expect(
        meetsContrastRequirement("#2563eb", "#ffffff", "AA", "normal")
      ).toBe(true);
      expect(
        meetsContrastRequirement("#dc2626", "#ffffff", "AA", "normal")
      ).toBe(true);

      // These should fail AA
      expect(
        meetsContrastRequirement("#cccccc", "#ffffff", "AA", "normal")
      ).toBe(false);
      expect(
        meetsContrastRequirement("#ffff00", "#ffffff", "AA", "normal")
      ).toBe(false);
    });

    test("should validate AA compliance for large text", () => {
      // Large text has lower requirements (3:1 minimum)
      expect(
        meetsContrastRequirement("#767676", "#ffffff", "AA", "large")
      ).toBe(true);
      expect(
        meetsContrastRequirement("#cccccc", "#ffffff", "AA", "large")
      ).toBe(false);
    });

    test("should validate AAA compliance", () => {
      // AAA has stricter requirements (7:1 for normal, 4.5:1 for large)
      expect(
        meetsContrastRequirement("#000000", "#ffffff", "AAA", "normal")
      ).toBe(true);
      expect(
        meetsContrastRequirement("#2563eb", "#ffffff", "AAA", "normal")
      ).toBe(false);
      expect(
        meetsContrastRequirement("#2563eb", "#ffffff", "AAA", "large")
      ).toBe(true);
    });
  });

  describe("Platform Color Palette", () => {
    const colors = {
      primary: "#2563eb",
      secondary: "#6b7280",
      success: "#047857", // Darker green that meets AA standards
      warning: "#b45309", // Darker orange that meets AA standards
      error: "#dc2626",
      text: "#1f2937",
      textMuted: "#6b7280",
      background: "#ffffff",
      backgroundSecondary: "#f9fafb",
    };

    test("should meet AA standards for primary colors on white", () => {
      expect(meetsContrastRequirement(colors.primary, colors.background)).toBe(
        true
      );
      expect(meetsContrastRequirement(colors.success, colors.background)).toBe(
        true
      );
      expect(meetsContrastRequirement(colors.warning, colors.background)).toBe(
        true
      );
      expect(meetsContrastRequirement(colors.error, colors.background)).toBe(
        true
      );
    });

    test("should meet AA standards for text colors", () => {
      expect(meetsContrastRequirement(colors.text, colors.background)).toBe(
        true
      );
      expect(
        meetsContrastRequirement(colors.textMuted, colors.background)
      ).toBe(true);
    });

    test("should meet AA standards for secondary backgrounds", () => {
      expect(
        meetsContrastRequirement(colors.text, colors.backgroundSecondary)
      ).toBe(true);
      expect(
        meetsContrastRequirement(colors.primary, colors.backgroundSecondary)
      ).toBe(true);
    });
  });

  describe("Dynamic Color Testing", () => {
    test("should validate user-generated color combinations", () => {
      const testCombinations = [
        { fg: "#ffffff", bg: "#2563eb", expected: true }, // White on blue
        { fg: "#000000", bg: "#ffff00", expected: true }, // Black on yellow
        { fg: "#ffffff", bg: "#cccccc", expected: false }, // White on light gray
        { fg: "#ff0000", bg: "#00ff00", expected: false }, // Red on green (problematic)
      ];

      testCombinations.forEach(({ fg, bg, expected }) => {
        const result = meetsContrastRequirement(fg, bg);
        expect(result).toBe(expected);
      });
    });
  });

  describe("Edge Cases", () => {
    test("should handle invalid color formats gracefully", () => {
      expect(getContrastRatio("invalid", "#ffffff")).toBe(1);
      expect(getContrastRatio("#ffffff", "invalid")).toBe(1);
      expect(getContrastRatio("", "")).toBe(1);
    });

    test("should handle transparent colors", () => {
      // Transparent colors should be treated as having no contrast
      expect(getContrastRatio("rgba(0,0,0,0)", "#ffffff")).toBe(1);
      expect(getContrastRatio("transparent", "#ffffff")).toBe(1);
    });
  });

  describe("Real-world UI Elements", () => {
    test("should validate button color combinations", () => {
      const buttonStyles = [
        { text: "#ffffff", bg: "#2563eb" }, // Primary button
        { text: "#374151", bg: "#f3f4f6" }, // Secondary button
        { text: "#ffffff", bg: "#dc2626" }, // Danger button
        { text: "#ffffff", bg: "#047857" }, // Success button (darker green)
      ];

      buttonStyles.forEach(({ text, bg }) => {
        expect(meetsContrastRequirement(text, bg)).toBe(true);
      });
    });

    test("should validate form element colors", () => {
      const formStyles = [
        { text: "#374151", bg: "#ffffff", border: "#d1d5db" },
        { text: "#dc2626", bg: "#ffffff", border: "#dc2626" }, // Error state
        { text: "#047857", bg: "#ffffff", border: "#047857" }, // Success state (darker green)
      ];

      formStyles.forEach(({ text, bg }) => {
        expect(meetsContrastRequirement(text, bg)).toBe(true);
      });
    });

    test("should validate link colors", () => {
      const linkStyles = [
        { link: "#1d4ed8", bg: "#ffffff" }, // Default link
        { link: "#1e40af", bg: "#ffffff" }, // Hover state
        { link: "#60a5fa", bg: "#111827" }, // Dark mode link
      ];

      linkStyles.forEach(({ link, bg }) => {
        expect(meetsContrastRequirement(link, bg)).toBe(true);
      });
    });
  });

  describe("Accessibility Warnings", () => {
    test("should identify potentially problematic color combinations", () => {
      const problematicCombinations = [
        { fg: "#ff0000", bg: "#00ff00" }, // Red on green (colorblind issues)
        { fg: "#0000ff", bg: "#ff0000" }, // Blue on red (vibrating colors)
        { fg: "#ffff00", bg: "#ffffff" }, // Yellow on white (low contrast)
      ];

      problematicCombinations.forEach(({ fg, bg }) => {
        const ratio = getContrastRatio(fg, bg);
        if (ratio < 4.5) {
          console.warn(
            `Low contrast detected: ${fg} on ${bg} (ratio: ${ratio.toFixed(2)})`
          );
        }
      });
    });
  });
});
