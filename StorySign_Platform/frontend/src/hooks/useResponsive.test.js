import { renderHook } from "@testing-library/react";
import {
  useResponsive,
  useMediaQuery,
  useDeviceCapabilities,
} from "./useResponsive";

// Mock window object for testing
const mockWindow = (width = 1024, height = 768) => {
  Object.defineProperty(window, "innerWidth", {
    writable: true,
    configurable: true,
    value: width,
  });
  Object.defineProperty(window, "innerHeight", {
    writable: true,
    configurable: true,
    value: height,
  });
};

// Mock matchMedia
const mockMatchMedia = (matches = false) => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
      matches,
      media: query,
      onchange: null,
      addListener: jest.fn(), // deprecated
      removeListener: jest.fn(), // deprecated
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
};

describe("useResponsive", () => {
  beforeEach(() => {
    mockMatchMedia();
  });

  test("should detect mobile device correctly", () => {
    mockWindow(375, 667); // iPhone dimensions

    const { result } = renderHook(() => useResponsive());

    expect(result.current.isMobile).toBe(true);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(false);
    expect(result.current.deviceType).toBe("mobile");
    expect(result.current.currentBreakpoint).toBe("xs");
  });

  test("should detect tablet device correctly", () => {
    mockWindow(768, 1024); // iPad dimensions

    const { result } = renderHook(() => useResponsive());

    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(true);
    expect(result.current.isDesktop).toBe(false);
    expect(result.current.deviceType).toBe("tablet");
    expect(result.current.currentBreakpoint).toBe("md");
  });

  test("should detect desktop device correctly", () => {
    mockWindow(1200, 800); // Desktop dimensions

    const { result } = renderHook(() => useResponsive());

    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(true);
    expect(result.current.deviceType).toBe("desktop");
    expect(result.current.currentBreakpoint).toBe("xl");
  });

  test("should detect orientation correctly", () => {
    // Portrait
    mockWindow(375, 667);
    const { result: portraitResult } = renderHook(() => useResponsive());
    expect(portraitResult.current.orientation).toBe("portrait");

    // Landscape
    mockWindow(667, 375);
    const { result: landscapeResult } = renderHook(() => useResponsive());
    expect(landscapeResult.current.orientation).toBe("landscape");
  });

  test("should provide correct breakpoint utilities", () => {
    mockWindow(800, 600); // md breakpoint

    const { result } = renderHook(() => useResponsive());

    expect(result.current.isBreakpointUp("sm")).toBe(true);
    expect(result.current.isBreakpointUp("lg")).toBe(false);
    expect(result.current.isBreakpointDown("lg")).toBe(true);
    expect(result.current.isBreakpointDown("sm")).toBe(false);
    expect(result.current.isBreakpointBetween("md", "lg")).toBe(true);
  });

  test("should provide responsive grid columns", () => {
    // Mobile
    mockWindow(375, 667);
    const { result: mobileResult } = renderHook(() => useResponsive());
    expect(mobileResult.current.getGridColumns()).toBe(1);

    // Tablet
    mockWindow(768, 1024);
    const { result: tabletResult } = renderHook(() => useResponsive());
    expect(tabletResult.current.getGridColumns()).toBe(2);

    // Desktop
    mockWindow(1200, 800);
    const { result: desktopResult } = renderHook(() => useResponsive());
    expect(desktopResult.current.getGridColumns()).toBe(3);
  });

  test("should determine sidebar collapse correctly", () => {
    // Mobile should collapse sidebar
    mockWindow(375, 667);
    const { result: mobileResult } = renderHook(() => useResponsive());
    expect(mobileResult.current.shouldCollapseSidebar).toBe(true);

    // Desktop should not collapse sidebar
    mockWindow(1200, 800);
    const { result: desktopResult } = renderHook(() => useResponsive());
    expect(desktopResult.current.shouldCollapseSidebar).toBe(false);
  });

  test("should determine video optimizations correctly", () => {
    // Mobile should use optimizations
    mockWindow(375, 667);
    const { result: mobileResult } = renderHook(() => useResponsive());
    expect(mobileResult.current.shouldUseVideoOptimizations).toBe(true);

    // Desktop should not use optimizations
    mockWindow(1200, 800);
    const { result: desktopResult } = renderHook(() => useResponsive());
    expect(desktopResult.current.shouldUseVideoOptimizations).toBe(false);
  });

  test("should provide appropriate video quality", () => {
    // Mobile should use medium quality
    mockWindow(375, 667);
    const { result: mobileResult } = renderHook(() => useResponsive());
    expect(mobileResult.current.getVideoQuality).toBe("medium");

    // Tablet should use high quality
    mockWindow(768, 1024);
    const { result: tabletResult } = renderHook(() => useResponsive());
    expect(tabletResult.current.getVideoQuality).toBe("high");

    // Desktop should use ultra quality
    mockWindow(1200, 800);
    const { result: desktopResult } = renderHook(() => useResponsive());
    expect(desktopResult.current.getVideoQuality).toBe("ultra");
  });
});

describe("useMediaQuery", () => {
  beforeEach(() => {
    mockMatchMedia();
  });

  test("should return correct media query result", () => {
    mockMatchMedia(true);

    const { result } = renderHook(() => useMediaQuery("(min-width: 768px)"));

    expect(result.current).toBe(true);
  });

  test("should return false for non-matching media query", () => {
    mockMatchMedia(false);

    const { result } = renderHook(() => useMediaQuery("(min-width: 1200px)"));

    expect(result.current).toBe(false);
  });
});

describe("useDeviceCapabilities", () => {
  beforeEach(() => {
    // Mock navigator
    Object.defineProperty(navigator, "onLine", {
      writable: true,
      value: true,
    });

    Object.defineProperty(navigator, "mediaDevices", {
      writable: true,
      value: {
        getUserMedia: jest.fn(),
      },
    });

    Object.defineProperty(navigator, "geolocation", {
      writable: true,
      value: {},
    });

    Object.defineProperty(navigator, "vibrate", {
      writable: true,
      value: jest.fn(),
    });

    Object.defineProperty(window, "Notification", {
      writable: true,
      value: jest.fn(),
    });

    Object.defineProperty(window, "DeviceOrientationEvent", {
      writable: true,
      value: jest.fn(),
    });
  });

  test("should detect device capabilities correctly", () => {
    const { result } = renderHook(() => useDeviceCapabilities());

    expect(result.current.hasCamera).toBe(true);
    expect(result.current.hasMicrophone).toBe(true);
    expect(result.current.hasGeolocation).toBe(true);
    expect(result.current.hasOrientation).toBe(true);
    expect(result.current.hasVibration).toBe(true);
    expect(result.current.hasNotifications).toBe(true);
    expect(result.current.isOnline).toBe(true);
  });

  test("should detect offline status", () => {
    Object.defineProperty(navigator, "onLine", {
      writable: true,
      value: false,
    });

    const { result } = renderHook(() => useDeviceCapabilities());

    expect(result.current.isOnline).toBe(false);
  });
});
