/**
 * Platform Service Implementation
 *
 * Provides the actual implementation of the PlatformService interface
 * for cross-module communication and platform-level operations.
 */

import { PlatformService, NotificationType } from "../types/module";

// Extend Performance interface to include Chrome-specific memory property
interface PerformanceWithMemory extends Performance {
  memory?: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
  };
}

export class PlatformServiceImpl implements PlatformService {
  private navigationCallback:
    | ((moduleId: string, params?: Record<string, any>) => void)
    | null = null;
  private notificationCallback:
    | ((message: string, type: NotificationType, duration?: number) => void)
    | null = null;
  private themeChangeCallback: ((theme: string) => void) | null = null;
  private accessibilityUpdateCallback:
    | ((settings: Record<string, any>) => void)
    | null = null;

  private currentTheme: string = "light";
  private accessibilitySettings: Record<string, any> = {
    fontSize: "medium",
    reducedMotion: false,
    highContrast: false,
    screenReader: false,
  };

  constructor() {
    console.log("PlatformServiceImpl: Initialized");
  }

  // Navigation
  navigateToModule(moduleId: string, params?: Record<string, any>): void {
    console.log(`PlatformService: Navigate to module ${moduleId}`, params);

    if (this.navigationCallback) {
      this.navigationCallback(moduleId, params);
    } else {
      console.warn("PlatformService: No navigation callback registered");

      // Fallback to browser navigation if available
      if (typeof window !== "undefined" && window.history) {
        const route = this.getModuleRoute(moduleId);
        if (route) {
          window.history.pushState({}, "", route);
        }
      }
    }
  }

  // Notifications
  showNotification(
    message: string,
    type: NotificationType = NotificationType.INFO,
    duration?: number
  ): void {
    console.log(`PlatformService: Show notification [${type}]: ${message}`);

    if (this.notificationCallback) {
      this.notificationCallback(message, type, duration);
    } else {
      console.warn("PlatformService: No notification callback registered");

      // Fallback to browser notification or console
      this.fallbackNotification(message, type);
    }
  }

  // Theme management
  getCurrentTheme(): string {
    return this.currentTheme;
  }

  changeTheme(theme: string): void {
    console.log(`PlatformService: Change theme to ${theme}`);

    this.currentTheme = theme;

    if (this.themeChangeCallback) {
      this.themeChangeCallback(theme);
    } else {
      console.warn("PlatformService: No theme change callback registered");

      // Fallback to direct CSS variable update
      this.fallbackThemeChange(theme);
    }
  }

  // Accessibility settings
  getAccessibilitySettings(): Record<string, any> {
    return { ...this.accessibilitySettings };
  }

  updateAccessibilitySettings(settings: Record<string, any>): void {
    console.log("PlatformService: Update accessibility settings", settings);

    this.accessibilitySettings = { ...this.accessibilitySettings, ...settings };

    if (this.accessibilityUpdateCallback) {
      this.accessibilityUpdateCallback(this.accessibilitySettings);
    } else {
      console.warn(
        "PlatformService: No accessibility update callback registered"
      );

      // Fallback to direct application
      this.fallbackAccessibilityUpdate(this.accessibilitySettings);
    }
  }

  // Callback registration methods (for platform shell integration)
  public setNavigationCallback(
    callback: (moduleId: string, params?: Record<string, any>) => void
  ): void {
    this.navigationCallback = callback;
    console.log("PlatformService: Navigation callback registered");
  }

  public setNotificationCallback(
    callback: (
      message: string,
      type: NotificationType,
      duration?: number
    ) => void
  ): void {
    this.notificationCallback = callback;
    console.log("PlatformService: Notification callback registered");
  }

  public setThemeChangeCallback(callback: (theme: string) => void): void {
    this.themeChangeCallback = callback;
    console.log("PlatformService: Theme change callback registered");
  }

  public setAccessibilityUpdateCallback(
    callback: (settings: Record<string, any>) => void
  ): void {
    this.accessibilityUpdateCallback = callback;
    console.log("PlatformService: Accessibility update callback registered");
  }

  // Additional utility methods
  public broadcastEvent(eventType: string, data: any): void {
    console.log(`PlatformService: Broadcasting event ${eventType}`, data);

    // Create and dispatch custom event
    if (typeof window !== "undefined") {
      const event = new CustomEvent(`platform:${eventType}`, {
        detail: data,
      });
      window.dispatchEvent(event);
    }
  }

  public subscribeToEvent(
    eventType: string,
    handler: (data: any) => void
  ): () => void {
    if (typeof window === "undefined") {
      console.warn(
        "PlatformService: Cannot subscribe to events - window not available"
      );
      return () => {};
    }

    const eventName = `platform:${eventType}`;
    const eventHandler = (event: CustomEvent) => {
      handler(event.detail);
    };

    window.addEventListener(eventName, eventHandler as EventListener);
    console.log(`PlatformService: Subscribed to event ${eventType}`);

    // Return unsubscribe function
    return () => {
      window.removeEventListener(eventName, eventHandler as EventListener);
      console.log(`PlatformService: Unsubscribed from event ${eventType}`);
    };
  }

  public getSystemInfo(): Record<string, any> {
    const info: Record<string, any> = {
      platform: "web",
      timestamp: new Date().toISOString(),
      theme: this.currentTheme,
      accessibility: this.accessibilitySettings,
    };

    if (typeof window !== "undefined") {
      info.userAgent = window.navigator.userAgent;
      info.language = window.navigator.language;
      info.viewport = {
        width: window.innerWidth,
        height: window.innerHeight,
      };
    }

    // Check for Chrome-specific memory API (not available in all browsers)
    const performanceWithMemory = performance as PerformanceWithMemory;
    if (typeof performance !== "undefined" && performanceWithMemory.memory) {
      info.memory = {
        used: performanceWithMemory.memory.usedJSHeapSize,
        total: performanceWithMemory.memory.totalJSHeapSize,
        limit: performanceWithMemory.memory.jsHeapSizeLimit,
      };
    }

    return info;
  }

  // Private helper methods
  private getModuleRoute(moduleId: string): string | null {
    const routeMap: Record<string, string> = {
      dashboard: "/",
      "asl-world": "/asl-world",
      harmony: "/harmony",
      reconnect: "/reconnect",
    };

    return routeMap[moduleId] || null;
  }

  private fallbackNotification(message: string, type: NotificationType): void {
    // Try browser notification API
    if (typeof window !== "undefined" && "Notification" in window) {
      if (Notification.permission === "granted") {
        new Notification(`StorySign - ${type.toUpperCase()}`, {
          body: message,
          icon: "/favicon.ico",
        });
        return;
      }
    }

    // Fallback to console with styling
    const styles: Record<NotificationType, string> = {
      [NotificationType.INFO]: "color: blue; font-weight: bold;",
      [NotificationType.SUCCESS]: "color: green; font-weight: bold;",
      [NotificationType.WARNING]: "color: orange; font-weight: bold;",
      [NotificationType.ERROR]: "color: red; font-weight: bold;",
    };

    console.log(`%c[${type.toUpperCase()}] ${message}`, styles[type]);
  }

  private fallbackThemeChange(theme: string): void {
    if (typeof document === "undefined") {
      return;
    }

    // Basic theme colors
    const themes: Record<string, Record<string, string>> = {
      light: {
        "--theme-primary": "#2196F3",
        "--theme-secondary": "#FFC107",
        "--theme-background": "#ffffff",
        "--theme-surface": "#f5f5f5",
        "--theme-text": "#333333",
        "--theme-textSecondary": "#666666",
      },
      dark: {
        "--theme-primary": "#64B5F6",
        "--theme-secondary": "#FFD54F",
        "--theme-background": "#121212",
        "--theme-surface": "#1e1e1e",
        "--theme-text": "#ffffff",
        "--theme-textSecondary": "#cccccc",
      },
      highContrast: {
        "--theme-primary": "#000000",
        "--theme-secondary": "#FFFF00",
        "--theme-background": "#ffffff",
        "--theme-surface": "#f0f0f0",
        "--theme-text": "#000000",
        "--theme-textSecondary": "#000000",
      },
    };

    const themeColors = themes[theme];
    if (themeColors) {
      const root = document.documentElement;
      Object.entries(themeColors).forEach(([property, value]) => {
        root.style.setProperty(property, value);
      });
    }
  }

  private fallbackAccessibilityUpdate(settings: Record<string, any>): void {
    if (typeof document === "undefined") {
      return;
    }

    const root = document.documentElement;

    // Font size
    if (settings.fontSize) {
      const fontSizeMap: Record<string, string> = {
        small: "14px",
        medium: "16px",
        large: "18px",
        xlarge: "20px",
      };
      root.style.setProperty(
        "--base-font-size",
        fontSizeMap[settings.fontSize] || "16px"
      );
    }

    // Reduced motion
    if (settings.reducedMotion !== undefined) {
      root.style.setProperty(
        "--animation-duration",
        settings.reducedMotion ? "0s" : "0.3s"
      );
      root.style.setProperty(
        "--transition-duration",
        settings.reducedMotion ? "0s" : "0.2s"
      );
    }

    // High contrast
    if (settings.highContrast && this.currentTheme !== "highContrast") {
      this.changeTheme("highContrast");
    }
  }
}

export default PlatformServiceImpl;
