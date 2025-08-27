import { useState, useEffect } from "react";

// Breakpoint definitions
const BREAKPOINTS = {
  xs: 0,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1400,
};

// Custom hook for responsive design
export const useResponsive = () => {
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== "undefined" ? window.innerWidth : 1200,
    height: typeof window !== "undefined" ? window.innerHeight : 800,
  });

  const [orientation, setOrientation] = useState(
    typeof window !== "undefined" && window.innerWidth > window.innerHeight
      ? "landscape"
      : "portrait"
  );

  const [isTouchDevice, setIsTouchDevice] = useState(false);

  useEffect(() => {
    // Check if it's a touch device
    const checkTouchDevice = () => {
      setIsTouchDevice(
        "ontouchstart" in window ||
          navigator.maxTouchPoints > 0 ||
          navigator.msMaxTouchPoints > 0
      );
    };

    checkTouchDevice();

    const handleResize = () => {
      const newWidth = window.innerWidth;
      const newHeight = window.innerHeight;

      setWindowSize({
        width: newWidth,
        height: newHeight,
      });

      setOrientation(newWidth > newHeight ? "landscape" : "portrait");
    };

    const handleOrientationChange = () => {
      // Small delay to ensure dimensions are updated
      setTimeout(() => {
        handleResize();
      }, 100);
    };

    window.addEventListener("resize", handleResize);
    window.addEventListener("orientationchange", handleOrientationChange);

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("orientationchange", handleOrientationChange);
    };
  }, []);

  // Get current breakpoint
  const getCurrentBreakpoint = () => {
    const width = windowSize.width;

    if (width >= BREAKPOINTS.xxl) return "xxl";
    if (width >= BREAKPOINTS.xl) return "xl";
    if (width >= BREAKPOINTS.lg) return "lg";
    if (width >= BREAKPOINTS.md) return "md";
    if (width >= BREAKPOINTS.sm) return "sm";
    return "xs";
  };

  // Check if current screen size is at or above a breakpoint
  const isBreakpointUp = (breakpoint) => {
    return windowSize.width >= BREAKPOINTS[breakpoint];
  };

  // Check if current screen size is below a breakpoint
  const isBreakpointDown = (breakpoint) => {
    return windowSize.width < BREAKPOINTS[breakpoint];
  };

  // Check if current screen size is between two breakpoints
  const isBreakpointBetween = (minBreakpoint, maxBreakpoint) => {
    return (
      windowSize.width >= BREAKPOINTS[minBreakpoint] &&
      windowSize.width < BREAKPOINTS[maxBreakpoint]
    );
  };

  // Convenience methods for common breakpoints
  const isMobile = isBreakpointDown("md"); // < 768px
  const isTablet = isBreakpointBetween("md", "lg"); // 768px - 991px
  const isDesktop = isBreakpointUp("lg"); // >= 992px
  const isLargeDesktop = isBreakpointUp("xl"); // >= 1200px

  // Device type detection
  const getDeviceType = () => {
    if (isMobile) return "mobile";
    if (isTablet) return "tablet";
    return "desktop";
  };

  // Check if device has limited screen space
  const isCompactDevice = () => {
    return isMobile || (isTablet && orientation === "portrait");
  };

  // Get responsive grid columns based on screen size
  const getGridColumns = (
    mobileColumns = 1,
    tabletColumns = 2,
    desktopColumns = 3
  ) => {
    if (isMobile) return mobileColumns;
    if (isTablet) return tabletColumns;
    return desktopColumns;
  };

  // Get responsive spacing based on screen size
  const getResponsiveSpacing = (
    mobileSpacing = 8,
    tabletSpacing = 16,
    desktopSpacing = 24
  ) => {
    if (isMobile) return mobileSpacing;
    if (isTablet) return tabletSpacing;
    return desktopSpacing;
  };

  // Check if sidebar should be collapsed by default
  const shouldCollapseSidebar = () => {
    return isMobile || (isTablet && orientation === "portrait");
  };

  // Get appropriate font size for current device
  const getResponsiveFontSize = (baseFontSize = 16) => {
    if (isMobile) return Math.max(14, baseFontSize - 2);
    if (isTablet) return baseFontSize;
    return baseFontSize;
  };

  // Check if video should use mobile optimizations
  const shouldUseVideoOptimizations = () => {
    return isMobile || (windowSize.width < 1024 && isTouchDevice);
  };

  // Get appropriate video quality based on device and connection
  const getVideoQuality = () => {
    if (isMobile) return "medium";
    if (isTablet) return "high";
    return "ultra";
  };

  return {
    // Window dimensions
    windowSize,
    orientation,
    isTouchDevice,

    // Breakpoint utilities
    currentBreakpoint: getCurrentBreakpoint(),
    isBreakpointUp,
    isBreakpointDown,
    isBreakpointBetween,

    // Device type checks
    isMobile,
    isTablet,
    isDesktop,
    isLargeDesktop,
    deviceType: getDeviceType(),
    isCompactDevice: isCompactDevice(),

    // Responsive utilities
    getGridColumns,
    getResponsiveSpacing,
    shouldCollapseSidebar: shouldCollapseSidebar(),
    getResponsiveFontSize,
    shouldUseVideoOptimizations: shouldUseVideoOptimizations(),
    getVideoQuality: getVideoQuality(),

    // Breakpoint constants
    breakpoints: BREAKPOINTS,
  };
};

// Hook for media queries
export const useMediaQuery = (query) => {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);

    const handleChange = (event) => {
      setMatches(event.matches);
    };

    mediaQuery.addEventListener("change", handleChange);

    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, [query]);

  return matches;
};

// Hook for detecting device capabilities
export const useDeviceCapabilities = () => {
  const [capabilities, setCapabilities] = useState({
    hasCamera: false,
    hasMicrophone: false,
    hasGeolocation: false,
    hasOrientation: false,
    hasVibration: false,
    hasNotifications: false,
    isOnline: typeof navigator !== "undefined" ? navigator.onLine : true,
  });

  useEffect(() => {
    const checkCapabilities = async () => {
      const newCapabilities = {
        hasCamera: !!(
          navigator.mediaDevices && navigator.mediaDevices.getUserMedia
        ),
        hasMicrophone: !!(
          navigator.mediaDevices && navigator.mediaDevices.getUserMedia
        ),
        hasGeolocation: !!navigator.geolocation,
        hasOrientation: !!window.DeviceOrientationEvent,
        hasVibration: !!navigator.vibrate,
        hasNotifications: !!window.Notification,
        isOnline: navigator.onLine,
      };

      setCapabilities(newCapabilities);
    };

    checkCapabilities();

    const handleOnlineStatusChange = () => {
      setCapabilities((prev) => ({
        ...prev,
        isOnline: navigator.onLine,
      }));
    };

    window.addEventListener("online", handleOnlineStatusChange);
    window.addEventListener("offline", handleOnlineStatusChange);

    return () => {
      window.removeEventListener("online", handleOnlineStatusChange);
      window.removeEventListener("offline", handleOnlineStatusChange);
    };
  }, []);

  return capabilities;
};

export default useResponsive;
