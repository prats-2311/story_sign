/**
 * Analytics Service
 * Frontend service for tracking user interactions and learning analytics
 */

import API_BASE_URL from "../config/api";

class AnalyticsService {
  constructor() {
    this.sessionId = this.generateSessionId();
    this.eventQueue = [];
    this.isProcessing = false;
    this.batchSize = 10;
    this.flushInterval = 5000; // 5 seconds
    this.consentStatus = null;

    // Start background processing
    this.startBackgroundProcessing();

    // Check consent status on initialization
    this.checkConsentStatus();
  }

  /**
   * Generate a unique session ID
   */
  generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Track a general analytics event
   */
  async trackEvent(eventType, moduleName, eventData, options = {}) {
    try {
      const event = {
        event_type: eventType,
        module_name: moduleName,
        event_data: {
          ...eventData,
          timestamp: new Date().toISOString(),
          url: window.location.href,
          user_agent: navigator.userAgent,
        },
        session_id: this.sessionId,
        processing_time_ms: options.processingTime,
        force_anonymous: options.forceAnonymous || false,
      };

      // Add to queue for batch processing
      this.eventQueue.push(event);

      // Flush immediately for critical events
      if (options.immediate) {
        await this.flushEvents();
      }

      return true;
    } catch (error) {
      console.error("Error tracking event:", error);
      return false;
    }
  }

  /**
   * Track user action (convenience method)
   */
  async trackUserAction(action, module, details = {}) {
    return this.trackEvent("feature_used", module, {
      action,
      details,
      page: window.location.pathname,
    });
  }

  /**
   * Track performance metric
   */
  async trackPerformance(metricName, metricValue, module, additionalData = {}) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/analytics/events/performance`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.getAuthToken()}`,
          },
          body: JSON.stringify({
            metric_name: metricName,
            metric_value: metricValue,
            module: module,
            session_id: this.sessionId,
            additional_data: additionalData,
          }),
        }
      );

      return response.ok;
    } catch (error) {
      console.error("Error tracking performance metric:", error);
      return false;
    }
  }

  /**
   * Track learning event
   */
  async trackLearningEvent(
    eventType,
    storyId = null,
    sentenceIndex = null,
    score = null,
    additionalData = {}
  ) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/analytics/events/learning`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.getAuthToken()}`,
          },
          body: JSON.stringify({
            event_type: eventType,
            session_id: this.sessionId,
            story_id: storyId,
            sentence_index: sentenceIndex,
            score: score,
            additional_data: additionalData,
          }),
        }
      );

      return response.ok;
    } catch (error) {
      console.error("Error tracking learning event:", error);
      return false;
    }
  }

  /**
   * Track page view
   */
  async trackPageView(pageName, additionalData = {}) {
    return this.trackEvent("page_view", "platform", {
      page_name: pageName,
      page_url: window.location.href,
      referrer: document.referrer,
      ...additionalData,
    });
  }

  /**
   * Track practice session start
   */
  async trackPracticeSessionStart(storyId, difficulty, sessionData = {}) {
    return this.trackLearningEvent(
      "practice_session_start",
      storyId,
      null,
      null,
      {
        difficulty,
        session_data: sessionData,
        started_at: new Date().toISOString(),
      }
    );
  }

  /**
   * Track practice session end
   */
  async trackPracticeSessionEnd(
    storyId,
    score,
    completedSentences,
    totalSentences,
    sessionData = {}
  ) {
    return this.trackLearningEvent(
      "practice_session_end",
      storyId,
      null,
      score,
      {
        completed_sentences: completedSentences,
        total_sentences: totalSentences,
        session_data: sessionData,
        ended_at: new Date().toISOString(),
      }
    );
  }

  /**
   * Track sentence attempt
   */
  async trackSentenceAttempt(
    storyId,
    sentenceIndex,
    score,
    feedback,
    attemptData = {}
  ) {
    return this.trackLearningEvent(
      "sentence_attempt",
      storyId,
      sentenceIndex,
      score,
      {
        feedback,
        attempt_data: attemptData,
        attempted_at: new Date().toISOString(),
      }
    );
  }

  /**
   * Track gesture detection
   */
  async trackGestureDetection(gestureData, confidence, processingTime) {
    return this.trackEvent(
      "gesture_detected",
      "asl_world",
      {
        gesture_data: gestureData,
        confidence: confidence,
        landmarks_count: gestureData.landmarks
          ? gestureData.landmarks.length
          : 0,
      },
      {
        processingTime: processingTime,
      }
    );
  }

  /**
   * Track AI feedback received
   */
  async trackAIFeedback(feedbackType, feedbackData, processingTime) {
    return this.trackEvent(
      "ai_feedback_received",
      "asl_world",
      {
        feedback_type: feedbackType,
        feedback_data: feedbackData,
        feedback_length: feedbackData.text ? feedbackData.text.length : 0,
      },
      {
        processingTime: processingTime,
      }
    );
  }

  /**
   * Track error occurrence
   */
  async trackError(errorType, errorMessage, errorData = {}) {
    return this.trackEvent(
      "error_occurred",
      "platform",
      {
        error_type: errorType,
        error_message: errorMessage,
        error_data: errorData,
        stack_trace: errorData.stack || null,
      },
      {
        immediate: true, // Flush errors immediately
      }
    );
  }

  /**
   * Manage user consent
   */
  async manageConsent(consentType, consentGiven, consentVersion = "1.0") {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analytics/consent`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.getAuthToken()}`,
        },
        body: JSON.stringify({
          consent_type: consentType,
          consent_given: consentGiven,
          consent_version: consentVersion,
        }),
      });

      if (response.ok) {
        // Update local consent status
        await this.checkConsentStatus();
        return true;
      }

      return false;
    } catch (error) {
      console.error("Error managing consent:", error);
      return false;
    }
  }

  /**
   * Check user consent status
   */
  async checkConsentStatus() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analytics/consent`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${this.getAuthToken()}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        this.consentStatus = data.consents;
        return this.consentStatus;
      }

      return null;
    } catch (error) {
      console.error("Error checking consent status:", error);
      return null;
    }
  }

  /**
   * Check if user has given specific consent
   */
  hasConsent(consentType) {
    if (!this.consentStatus) return false;

    const consent = this.consentStatus.find(
      c => c.consent_type === consentType && c.is_active
    );

    return consent && consent.consent_given;
  }

  /**
   * Get user analytics data
   */
  async getUserAnalytics(
    startDate = null,
    endDate = null,
    eventTypes = null,
    includeRawEvents = false
  ) {
    try {
      const params = new URLSearchParams();
      if (startDate) params.append("start_date", startDate.toISOString());
      if (endDate) params.append("end_date", endDate.toISOString());
      if (eventTypes) params.append("event_types", eventTypes.join(","));
      if (includeRawEvents) params.append("include_raw_events", "true");

      const response = await fetch(
        `${API_BASE_URL}/api/v1/analytics/user/me?${params}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${this.getAuthToken()}`,
          },
        }
      );

      if (response.ok) {
        return await response.json();
      }

      return null;
    } catch (error) {
      console.error("Error getting user analytics:", error);
      return null;
    }
  }

  /**
   * Export user data (GDPR compliance)
   */
  async exportUserData() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analytics/export`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${this.getAuthToken()}`,
        },
      });

      if (response.ok) {
        return await response.json();
      }

      return null;
    } catch (error) {
      console.error("Error exporting user data:", error);
      return null;
    }
  }

  /**
   * Delete user data (GDPR right to be forgotten)
   */
  async deleteUserData() {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/analytics/user-data`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${this.getAuthToken()}`,
          },
        }
      );

      return response.ok;
    } catch (error) {
      console.error("Error deleting user data:", error);
      return false;
    }
  }

  /**
   * Flush queued events to server
   */
  async flushEvents() {
    if (this.eventQueue.length === 0 || this.isProcessing) {
      return;
    }

    this.isProcessing = true;

    try {
      // Process events in batches
      while (this.eventQueue.length > 0) {
        const batch = this.eventQueue.splice(0, this.batchSize);

        for (const event of batch) {
          await this.sendEvent(event);
        }
      }
    } catch (error) {
      console.error("Error flushing events:", error);
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Send individual event to server
   */
  async sendEvent(event) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analytics/events`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.getAuthToken()}`,
        },
        body: JSON.stringify(event),
      });

      return response.ok;
    } catch (error) {
      console.error("Error sending event:", error);
      return false;
    }
  }

  /**
   * Start background event processing
   */
  startBackgroundProcessing() {
    // Flush events periodically
    setInterval(() => {
      this.flushEvents();
    }, this.flushInterval);

    // Flush events before page unload
    window.addEventListener("beforeunload", () => {
      // Use sendBeacon for reliable delivery during page unload
      if (this.eventQueue.length > 0) {
        const events = this.eventQueue.splice(0);
        for (const event of events) {
          navigator.sendBeacon(
            `${API_BASE_URL}/api/v1/analytics/events`,
            JSON.stringify(event)
          );
        }
      }
    });

    // Track page visibility changes
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        this.flushEvents();
      }
    });
  }

  /**
   * Get authentication token
   */
  getAuthToken() {
    return (
      localStorage.getItem("auth_token") || sessionStorage.getItem("auth_token")
    );
  }

  /**
   * Performance timing helper
   */
  createPerformanceTimer() {
    const startTime = performance.now();

    return {
      end: () => performance.now() - startTime,
      endAndTrack: (metricName, module, additionalData = {}) => {
        const duration = performance.now() - startTime;
        this.trackPerformance(metricName, duration, module, additionalData);
        return duration;
      },
    };
  }

  /**
   * Batch multiple events for efficient processing
   */
  batchEvents(events) {
    this.eventQueue.push(...events);
  }

  /**
   * Get service health status
   */
  async getHealthStatus() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analytics/health`);
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error("Error checking analytics health:", error);
      return null;
    }
  }
}

// Create singleton instance
const analyticsService = new AnalyticsService();

export default analyticsService;
