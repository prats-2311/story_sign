// PWA Service for managing Progressive Web App functionality
class PWAService {
  constructor() {
    this.isSupported = "serviceWorker" in navigator;
    this.registration = null;
    this.deferredPrompt = null;
    this.isInstalled = false;
    this.isOnline = navigator.onLine;

    this.init();
  }

  async init() {
    if (!this.isSupported) {
      console.warn("PWA: Service Workers not supported");
      return;
    }

    try {
      // Register service worker
      await this.registerServiceWorker();

      // Set up event listeners
      this.setupEventListeners();

      // Check if app is already installed
      this.checkInstallStatus();

      console.log("PWA: Service initialized successfully");
    } catch (error) {
      console.error("PWA: Initialization failed:", error);
    }
  }

  async registerServiceWorker() {
    try {
      // Check if service worker file exists first
      const response = await fetch("/sw.js", { method: "HEAD" });
      if (!response.ok) {
        throw new Error(`Service Worker file not found: ${response.status}`);
      }

      this.registration = await navigator.serviceWorker.register("/sw.js", {
        scope: "/",
      });

      console.log("PWA: Service Worker registered successfully");

      // Handle service worker updates
      this.registration.addEventListener("updatefound", () => {
        const newWorker = this.registration.installing;

        newWorker.addEventListener("statechange", () => {
          if (
            newWorker.state === "installed" &&
            navigator.serviceWorker.controller
          ) {
            // New service worker is available
            this.notifyUpdate();
          }
        });
      });

      return this.registration;
    } catch (error) {
      console.error("PWA: Service Worker registration failed:", error);
      throw error;
    }
  }

  setupEventListeners() {
    // Install prompt handling
    window.addEventListener("beforeinstallprompt", event => {
      event.preventDefault();
      this.deferredPrompt = event;
      console.log("PWA: Install prompt available");

      // Dispatch custom event for UI components
      window.dispatchEvent(new CustomEvent("pwa-install-available"));
    });

    // App installed handling
    window.addEventListener("appinstalled", () => {
      this.isInstalled = true;
      this.deferredPrompt = null;
      console.log("PWA: App installed successfully");

      // Dispatch custom event
      window.dispatchEvent(new CustomEvent("pwa-installed"));
    });

    // Online/offline status
    window.addEventListener("online", () => {
      this.isOnline = true;
      console.log("PWA: Back online");
      window.dispatchEvent(new CustomEvent("pwa-online"));
    });

    window.addEventListener("offline", () => {
      this.isOnline = false;
      console.log("PWA: Gone offline");
      window.dispatchEvent(new CustomEvent("pwa-offline"));
    });

    // Visibility change for background sync
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden && this.isOnline) {
        this.triggerBackgroundSync();
      }
    });
  }

  checkInstallStatus() {
    // Check if running in standalone mode (installed)
    if (
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true
    ) {
      this.isInstalled = true;
    }
  }

  // Install the PWA
  async installApp() {
    if (!this.deferredPrompt) {
      throw new Error("Install prompt not available");
    }

    try {
      this.deferredPrompt.prompt();
      const { outcome } = await this.deferredPrompt.userChoice;

      console.log("PWA: Install prompt result:", outcome);

      if (outcome === "accepted") {
        this.deferredPrompt = null;
        return true;
      }

      return false;
    } catch (error) {
      console.error("PWA: Install failed:", error);
      throw error;
    }
  }

  // Check if app can be installed
  canInstall() {
    return !!this.deferredPrompt && !this.isInstalled;
  }

  // Update service worker
  async updateServiceWorker() {
    if (!this.registration) {
      throw new Error("Service Worker not registered");
    }

    try {
      await this.registration.update();

      if (this.registration.waiting) {
        // Tell the waiting service worker to skip waiting
        this.registration.waiting.postMessage({ type: "SKIP_WAITING" });

        // Reload the page to activate the new service worker
        window.location.reload();
      }
    } catch (error) {
      console.error("PWA: Service Worker update failed:", error);
      throw error;
    }
  }

  // Notify about available update
  notifyUpdate() {
    console.log("PWA: Update available");
    window.dispatchEvent(new CustomEvent("pwa-update-available"));
  }

  // Cache important resources
  async cacheResources(urls) {
    if (!this.registration || !this.registration.active) {
      console.warn("PWA: Service Worker not active, cannot cache resources");
      return;
    }

    try {
      this.registration.active.postMessage({
        type: "CACHE_URLS",
        urls: urls,
      });

      console.log("PWA: Resources cached successfully");
    } catch (error) {
      console.error("PWA: Failed to cache resources:", error);
    }
  }

  // Trigger background sync
  async triggerBackgroundSync() {
    if (!this.registration || !this.registration.sync) {
      console.warn("PWA: Background Sync not supported");
      return;
    }

    try {
      await this.registration.sync.register("background-sync-practice-data");
      await this.registration.sync.register("background-sync-analytics");

      console.log("PWA: Background sync triggered");
    } catch (error) {
      console.error("PWA: Background sync failed:", error);
    }
  }

  // Store data for offline use
  async storeOfflineData(key, data) {
    try {
      if ("indexedDB" in window) {
        await this.storeInIndexedDB(key, data);
      } else {
        // Fallback to localStorage
        localStorage.setItem(`storysign_offline_${key}`, JSON.stringify(data));
      }

      console.log("PWA: Data stored for offline use");
    } catch (error) {
      console.error("PWA: Failed to store offline data:", error);
    }
  }

  // Retrieve offline data
  async getOfflineData(key) {
    try {
      if ("indexedDB" in window) {
        return await this.getFromIndexedDB(key);
      } else {
        // Fallback to localStorage
        const data = localStorage.getItem(`storysign_offline_${key}`);
        return data ? JSON.parse(data) : null;
      }
    } catch (error) {
      console.error("PWA: Failed to retrieve offline data:", error);
      return null;
    }
  }

  // IndexedDB operations (simplified)
  async storeInIndexedDB(key, data) {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open("StorySignOffline", 1);

      request.onerror = () => reject(request.error);

      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction(["offline_data"], "readwrite");
        const store = transaction.objectStore("offline_data");

        store.put({ key, data, timestamp: Date.now() });

        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
      };

      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains("offline_data")) {
          db.createObjectStore("offline_data", { keyPath: "key" });
        }
      };
    });
  }

  async getFromIndexedDB(key) {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open("StorySignOffline", 1);

      request.onerror = () => reject(request.error);

      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction(["offline_data"], "readonly");
        const store = transaction.objectStore("offline_data");
        const getRequest = store.get(key);

        getRequest.onsuccess = () => {
          const result = getRequest.result;
          resolve(result ? result.data : null);
        };

        getRequest.onerror = () => reject(getRequest.error);
      };
    });
  }

  // Request notification permission
  async requestNotificationPermission() {
    if (!("Notification" in window)) {
      throw new Error("Notifications not supported");
    }

    if (Notification.permission === "granted") {
      return true;
    }

    if (Notification.permission === "denied") {
      throw new Error("Notification permission denied");
    }

    const permission = await Notification.requestPermission();
    return permission === "granted";
  }

  // Show local notification
  async showNotification(title, options = {}) {
    if (!("Notification" in window)) {
      console.warn("PWA: Notifications not supported");
      return;
    }

    if (Notification.permission !== "granted") {
      console.warn("PWA: Notification permission not granted");
      return;
    }

    const defaultOptions = {
      icon: "/icon-192.png",
      badge: "/icon-192.png",
      vibrate: [100, 50, 100],
      ...options,
    };

    try {
      if (this.registration) {
        // Use service worker to show notification
        await this.registration.showNotification(title, defaultOptions);
      } else {
        // Fallback to regular notification
        new Notification(title, defaultOptions);
      }
    } catch (error) {
      console.error("PWA: Failed to show notification:", error);
    }
  }

  // Get app info
  getAppInfo() {
    return {
      isSupported: this.isSupported,
      isInstalled: this.isInstalled,
      canInstall: this.canInstall(),
      isOnline: this.isOnline,
      hasServiceWorker: !!this.registration,
      hasNotificationPermission:
        "Notification" in window && Notification.permission === "granted",
    };
  }

  // Cleanup
  destroy() {
    if (this.registration) {
      this.registration.unregister();
    }
  }
}

// Create singleton instance
const pwaService = new PWAService();

export default pwaService;
