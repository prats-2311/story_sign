/**
 * React hook for cross-platform synchronization
 */

import { useState, useEffect, useCallback, useRef } from "react";
import syncService from "../services/SyncService";

export const useSync = (options = {}) => {
  const [syncStatus, setSyncStatus] = useState(syncService.getStatus());
  const [conflicts, setConflicts] = useState([]);
  const [syncMetrics, setSyncMetrics] = useState(null);
  const [lastSyncTime, setLastSyncTime] = useState(null);

  const listenerRef = useRef(null);
  const autoSyncRef = useRef(null);

  // Sync event listener
  useEffect(() => {
    const handleSyncEvent = (event, data) => {
      switch (event) {
        case "sync_started":
          setSyncStatus((prev) => ({ ...prev, syncInProgress: true }));
          break;

        case "sync_completed":
          setSyncStatus((prev) => ({ ...prev, syncInProgress: false }));
          setLastSyncTime(new Date());
          break;

        case "sync_failed":
          setSyncStatus((prev) => ({ ...prev, syncInProgress: false }));
          console.error("Sync failed:", data.error);
          break;

        case "conflict_detected":
          setConflicts((prev) => [...prev, data]);
          break;

        case "online":
          setSyncStatus((prev) => ({ ...prev, isOnline: true }));
          break;

        case "offline":
          setSyncStatus((prev) => ({ ...prev, isOnline: false }));
          break;

        case "remote_sync_update":
          // Handle remote updates
          if (options.onRemoteUpdate) {
            options.onRemoteUpdate(data);
          }
          break;

        case "session_terminated":
          setSyncStatus((prev) => ({ ...prev, hasActiveSession: false }));
          break;

        default:
          break;
      }
    };

    listenerRef.current = handleSyncEvent;
    syncService.addSyncListener(handleSyncEvent);

    return () => {
      if (listenerRef.current) {
        syncService.removeSyncListener(listenerRef.current);
      }
    };
  }, [options.onRemoteUpdate]);

  // Auto-sync setup
  useEffect(() => {
    if (options.autoSync && options.autoSyncInterval) {
      autoSyncRef.current = setInterval(() => {
        if (syncStatus.isOnline && !syncStatus.syncInProgress) {
          syncService.triggerSync();
        }
      }, options.autoSyncInterval);

      return () => {
        if (autoSyncRef.current) {
          clearInterval(autoSyncRef.current);
        }
      };
    }
  }, [
    options.autoSync,
    options.autoSyncInterval,
    syncStatus.isOnline,
    syncStatus.syncInProgress,
  ]);

  // Load metrics on mount
  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const metrics = await syncService.getSyncMetrics();
        setSyncMetrics(metrics);
      } catch (error) {
        console.error("Failed to load sync metrics:", error);
      }
    };

    loadMetrics();
  }, []);

  // Create session
  const createSession = useCallback(async (sessionData = {}) => {
    try {
      const session = await syncService.createSession(sessionData);
      setSyncStatus((prev) => ({ ...prev, hasActiveSession: true }));
      return session;
    } catch (error) {
      console.error("Failed to create session:", error);
      throw error;
    }
  }, []);

  // Sync data
  const syncData = useCallback(async (data, options = {}) => {
    try {
      const result = await syncService.syncData(data, options);
      return result;
    } catch (error) {
      console.error("Failed to sync data:", error);
      throw error;
    }
  }, []);

  // Queue operation
  const queueOperation = useCallback(async (type, data, priority = 1) => {
    try {
      const operationId = await syncService.queueSyncOperation(
        type,
        data,
        priority
      );
      return operationId;
    } catch (error) {
      console.error("Failed to queue operation:", error);
      throw error;
    }
  }, []);

  // Process offline changes
  const processOfflineChanges = useCallback(async () => {
    try {
      const result = await syncService.processOfflineChanges();
      setSyncStatus((prev) => ({
        ...prev,
        offlineChangesCount: prev.offlineChangesCount - result.processed,
      }));
      return result;
    } catch (error) {
      console.error("Failed to process offline changes:", error);
      throw error;
    }
  }, []);

  // Resolve conflict
  const resolveConflict = useCallback(async (conflictId, resolution) => {
    try {
      await syncService.apiCall("/sync/resolve-conflict", "POST", {
        conflict_id: conflictId,
        resolution_strategy: resolution.strategy,
        resolved_value: resolution.value,
      });

      // Remove resolved conflict from state
      setConflicts((prev) => prev.filter((c) => c.id !== conflictId));

      return true;
    } catch (error) {
      console.error("Failed to resolve conflict:", error);
      throw error;
    }
  }, []);

  // Register conflict handler
  const registerConflictHandler = useCallback((fieldName, handler) => {
    syncService.registerConflictHandler(fieldName, handler);
  }, []);

  // Get sessions
  const getSessions = useCallback(async () => {
    try {
      return await syncService.getSessions();
    } catch (error) {
      console.error("Failed to get sessions:", error);
      return [];
    }
  }, []);

  // Terminate session
  const terminateSession = useCallback(async (sessionId) => {
    try {
      const success = await syncService.terminateSession(sessionId);
      if (success) {
        setSyncStatus((prev) => ({ ...prev, hasActiveSession: false }));
      }
      return success;
    } catch (error) {
      console.error("Failed to terminate session:", error);
      return false;
    }
  }, []);

  // Refresh status
  const refreshStatus = useCallback(() => {
    setSyncStatus(syncService.getStatus());
  }, []);

  // Refresh metrics
  const refreshMetrics = useCallback(async () => {
    try {
      const metrics = await syncService.getSyncMetrics();
      setSyncMetrics(metrics);
      return metrics;
    } catch (error) {
      console.error("Failed to refresh metrics:", error);
      return null;
    }
  }, []);

  return {
    // State
    syncStatus,
    conflicts,
    syncMetrics,
    lastSyncTime,

    // Actions
    createSession,
    syncData,
    queueOperation,
    processOfflineChanges,
    resolveConflict,
    registerConflictHandler,
    getSessions,
    terminateSession,
    refreshStatus,
    refreshMetrics,

    // Computed values
    isOnline: syncStatus.isOnline,
    hasActiveSession: syncStatus.hasActiveSession,
    syncInProgress: syncStatus.syncInProgress,
    hasOfflineChanges: syncStatus.offlineChangesCount > 0,
    hasQueuedOperations: syncStatus.queuedOperationsCount > 0,
    hasConflicts: conflicts.length > 0,
  };
};

// Hook for device-specific sync optimization
export const useSyncOptimization = () => {
  const [bandwidthProfile, setBandwidthProfile] = useState("medium");
  const [compressionEnabled, setCompressionEnabled] = useState(false);

  useEffect(() => {
    const status = syncService.getStatus();
    setBandwidthProfile(status.bandwidthProfile);
    setCompressionEnabled(status.bandwidthProfile === "low");
  }, []);

  const optimizeForBandwidth = useCallback((profile) => {
    setBandwidthProfile(profile);
    setCompressionEnabled(profile === "low");

    // Update sync service configuration
    syncService.bandwidthProfile = profile;
  }, []);

  const getOptimizationRecommendations = useCallback(() => {
    const status = syncService.getStatus();
    const recommendations = [];

    if (status.bandwidthProfile === "low") {
      recommendations.push({
        type: "compression",
        message:
          "Enable data compression for better performance on slow connections",
        action: () => setCompressionEnabled(true),
      });
    }

    if (status.offlineChangesCount > 10) {
      recommendations.push({
        type: "batch_sync",
        message: "Consider batching offline changes for better efficiency",
        action: () => syncService.processOfflineChanges(),
      });
    }

    return recommendations;
  }, []);

  return {
    bandwidthProfile,
    compressionEnabled,
    optimizeForBandwidth,
    getOptimizationRecommendations,
  };
};

// Hook for conflict management
export const useConflictResolution = () => {
  const [pendingConflicts, setPendingConflicts] = useState([]);
  const [resolutionStrategies, setResolutionStrategies] = useState({});

  useEffect(() => {
    const loadConflicts = async () => {
      try {
        const response = await syncService.apiCall("/sync/conflicts", "GET");
        if (response.success) {
          setPendingConflicts(response.conflicts);
        }
      } catch (error) {
        console.error("Failed to load conflicts:", error);
      }
    };

    loadConflicts();
  }, []);

  const setResolutionStrategy = useCallback((conflictType, strategy) => {
    setResolutionStrategies((prev) => ({
      ...prev,
      [conflictType]: strategy,
    }));
  }, []);

  const resolveConflictBatch = useCallback(async (conflicts, strategy) => {
    const results = [];

    for (const conflict of conflicts) {
      try {
        await syncService.apiCall("/sync/resolve-conflict", "POST", {
          conflict_id: conflict.id,
          resolution_strategy: strategy,
          resolved_value:
            strategy === "server_wins"
              ? conflict.server_value
              : conflict.client_value,
        });

        results.push({ conflict: conflict.id, success: true });
      } catch (error) {
        results.push({
          conflict: conflict.id,
          success: false,
          error: error.message,
        });
      }
    }

    // Update pending conflicts
    const resolvedIds = results.filter((r) => r.success).map((r) => r.conflict);
    setPendingConflicts((prev) =>
      prev.filter((c) => !resolvedIds.includes(c.id))
    );

    return results;
  }, []);

  const getConflictSummary = useCallback(() => {
    const summary = {
      total: pendingConflicts.length,
      byType: {},
      byField: {},
    };

    pendingConflicts.forEach((conflict) => {
      summary.byType[conflict.conflict_type] =
        (summary.byType[conflict.conflict_type] || 0) + 1;
      summary.byField[conflict.field_name] =
        (summary.byField[conflict.field_name] || 0) + 1;
    });

    return summary;
  }, [pendingConflicts]);

  return {
    pendingConflicts,
    resolutionStrategies,
    setResolutionStrategy,
    resolveConflictBatch,
    getConflictSummary,
  };
};

export default useSync;
