/**
 * useAnalytics Hook
 * React hook for easy analytics integration in components
 */

import { useEffect, useCallback, useRef } from "react";
import analyticsService from "../services/AnalyticsService";

export const useAnalytics = (moduleName = "platform") => {
  const performanceTimers = useRef(new Map());

  // Track component mount
  useEffect(() => {
    analyticsService.trackEvent("component_mounted", moduleName, {
      component: "unknown", // This would be set by the component
      mount_time: new Date().toISOString(),
    });

    return () => {
      // Track component unmount
      analyticsService.trackEvent("component_unmounted", moduleName, {
        component: "unknown",
        unmount_time: new Date().toISOString(),
      });
    };
  }, [moduleName]);

  // Track user action
  const trackAction = useCallback(
    (action, details = {}) => {
      return analyticsService.trackUserAction(action, moduleName, details);
    },
    [moduleName]
  );

  // Track page view
  const trackPageView = useCallback(
    (pageName, additionalData = {}) => {
      return analyticsService.trackPageView(pageName, {
        module: moduleName,
        ...additionalData,
      });
    },
    [moduleName]
  );

  // Track performance metric
  const trackPerformance = useCallback(
    (metricName, metricValue, additionalData = {}) => {
      return analyticsService.trackPerformance(
        metricName,
        metricValue,
        moduleName,
        additionalData
      );
    },
    [moduleName]
  );

  // Start performance timer
  const startTimer = useCallback((timerName) => {
    const timer = analyticsService.createPerformanceTimer();
    performanceTimers.current.set(timerName, timer);
    return timer;
  }, []);

  // End performance timer and track
  const endTimer = useCallback(
    (timerName, metricName = null, additionalData = {}) => {
      const timer = performanceTimers.current.get(timerName);
      if (timer) {
        const duration = timer.endAndTrack(
          metricName || `${timerName}_duration`,
          moduleName,
          additionalData
        );
        performanceTimers.current.delete(timerName);
        return duration;
      }
      return null;
    },
    [moduleName]
  );

  // Track error
  const trackError = useCallback(
    (errorType, errorMessage, errorData = {}) => {
      return analyticsService.trackError(errorType, errorMessage, {
        module: moduleName,
        ...errorData,
      });
    },
    [moduleName]
  );

  // Track learning event
  const trackLearningEvent = useCallback(
    (
      eventType,
      storyId = null,
      sentenceIndex = null,
      score = null,
      additionalData = {}
    ) => {
      return analyticsService.trackLearningEvent(
        eventType,
        storyId,
        sentenceIndex,
        score,
        {
          module: moduleName,
          ...additionalData,
        }
      );
    },
    [moduleName]
  );

  // Track gesture detection
  const trackGesture = useCallback(
    (gestureData, confidence, processingTime) => {
      return analyticsService.trackGestureDetection(
        gestureData,
        confidence,
        processingTime
      );
    },
    []
  );

  // Track AI feedback
  const trackAIFeedback = useCallback(
    (feedbackType, feedbackData, processingTime) => {
      return analyticsService.trackAIFeedback(
        feedbackType,
        feedbackData,
        processingTime
      );
    },
    []
  );

  return {
    trackAction,
    trackPageView,
    trackPerformance,
    trackError,
    trackLearningEvent,
    trackGesture,
    trackAIFeedback,
    startTimer,
    endTimer,
    analyticsService,
  };
};

// Specialized hooks for different modules
export const useASLWorldAnalytics = () => {
  const analytics = useAnalytics("asl_world");

  const trackPracticeStart = useCallback(
    (storyId, difficulty, sessionData = {}) => {
      return analytics.analyticsService.trackPracticeSessionStart(
        storyId,
        difficulty,
        sessionData
      );
    },
    [analytics]
  );

  const trackPracticeEnd = useCallback(
    (storyId, score, completedSentences, totalSentences, sessionData = {}) => {
      return analytics.analyticsService.trackPracticeSessionEnd(
        storyId,
        score,
        completedSentences,
        totalSentences,
        sessionData
      );
    },
    [analytics]
  );

  const trackSentenceAttempt = useCallback(
    (storyId, sentenceIndex, score, feedback, attemptData = {}) => {
      return analytics.analyticsService.trackSentenceAttempt(
        storyId,
        sentenceIndex,
        score,
        feedback,
        attemptData
      );
    },
    [analytics]
  );

  const trackStoryGeneration = useCallback(
    (prompt, generatedStory, processingTime) => {
      return analytics.trackAction("story_generated", {
        prompt_length: prompt.length,
        story_length: generatedStory.length,
        sentences_count: generatedStory.split(".").length,
        processing_time: processingTime,
      });
    },
    [analytics]
  );

  const trackVideoProcessing = useCallback(
    (frameData, processingTime) => {
      return analytics.trackPerformance(
        "video_processing_time",
        processingTime,
        {
          frame_size: frameData.size || 0,
          landmarks_detected: frameData.landmarks
            ? frameData.landmarks.length
            : 0,
        }
      );
    },
    [analytics]
  );

  return {
    ...analytics,
    trackPracticeStart,
    trackPracticeEnd,
    trackSentenceAttempt,
    trackStoryGeneration,
    trackVideoProcessing,
  };
};

export const usePluginAnalytics = () => {
  const analytics = useAnalytics("plugins");

  const trackPluginInstall = useCallback(
    (pluginId, pluginName, version) => {
      return analytics.trackAction("plugin_installed", {
        plugin_id: pluginId,
        plugin_name: pluginName,
        version: version,
      });
    },
    [analytics]
  );

  const trackPluginActivation = useCallback(
    (pluginId, pluginName) => {
      return analytics.trackAction("plugin_activated", {
        plugin_id: pluginId,
        plugin_name: pluginName,
      });
    },
    [analytics]
  );

  const trackPluginError = useCallback(
    (pluginId, errorType, errorMessage) => {
      return analytics.trackError("plugin_error", errorMessage, {
        plugin_id: pluginId,
        error_type: errorType,
      });
    },
    [analytics]
  );

  return {
    ...analytics,
    trackPluginInstall,
    trackPluginActivation,
    trackPluginError,
  };
};

export const useCollaborativeAnalytics = () => {
  const analytics = useAnalytics("collaborative");

  const trackSessionJoin = useCallback(
    (sessionId, participantCount) => {
      return analytics.trackAction("session_joined", {
        session_id: sessionId,
        participant_count: participantCount,
      });
    },
    [analytics]
  );

  const trackSessionLeave = useCallback(
    (sessionId, sessionDuration) => {
      return analytics.trackAction("session_left", {
        session_id: sessionId,
        session_duration: sessionDuration,
      });
    },
    [analytics]
  );

  const trackPeerFeedback = useCallback(
    (sessionId, feedbackType, feedbackData) => {
      return analytics.trackAction("peer_feedback_given", {
        session_id: sessionId,
        feedback_type: feedbackType,
        feedback_data: feedbackData,
      });
    },
    [analytics]
  );

  return {
    ...analytics,
    trackSessionJoin,
    trackSessionLeave,
    trackPeerFeedback,
  };
};

// Higher-order component for automatic analytics tracking
export const withAnalytics = (WrappedComponent, moduleName = "platform") => {
  return function AnalyticsWrappedComponent(props) {
    const analytics = useAnalytics(moduleName);

    // Track component render
    useEffect(() => {
      analytics.trackAction("component_rendered", {
        component_name: WrappedComponent.name || "UnknownComponent",
        props_keys: Object.keys(props),
      });
    }, [analytics, props]);

    return <WrappedComponent {...props} analytics={analytics} />;
  };
};

// Hook for consent management
export const useAnalyticsConsent = () => {
  const manageConsent = useCallback(
    (consentType, consentGiven, consentVersion = "1.0") => {
      return analyticsService.manageConsent(
        consentType,
        consentGiven,
        consentVersion
      );
    },
    []
  );

  const checkConsent = useCallback((consentType) => {
    return analyticsService.hasConsent(consentType);
  }, []);

  const getConsentStatus = useCallback(() => {
    return analyticsService.checkConsentStatus();
  }, []);

  const exportUserData = useCallback(() => {
    return analyticsService.exportUserData();
  }, []);

  const deleteUserData = useCallback(() => {
    return analyticsService.deleteUserData();
  }, []);

  return {
    manageConsent,
    checkConsent,
    getConsentStatus,
    exportUserData,
    deleteUserData,
  };
};

export default useAnalytics;
