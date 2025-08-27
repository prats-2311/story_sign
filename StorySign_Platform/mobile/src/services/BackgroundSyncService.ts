import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-netinfo';
import {AppState, AppStateStatus} from 'react-native';

interface SyncData {
  id: string;
  type: 'practice-session' | 'progress-update' | 'user-preferences' | 'content-download';
  data: any;
  timestamp: number;
  retryCount: number;
  priority: 'high' | 'normal' | 'low';
}

interface SyncConfig {
  maxRetries: number;
  retryDelay: number;
  batchSize: number;
  syncInterval: number;
}

class BackgroundSyncServiceClass {
  private isInitialized = false;
  private syncQueue: SyncData[] = [];
  private isOnline = true;
  private isSyncing = false;
  private syncTimer: NodeJS.Timeout | null = null;
  private appState: AppStateStatus = 'active';

  private config: SyncConfig = {
    maxRetries: 3,
    retryDelay: 5000, // 5 seconds
    batchSize: 10,
    syncInterval: 30000, // 30 seconds
  };

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Load pending sync items from storage
      await this.loadSyncQueue();

      // Setup network listener
      this.setupNetworkListener();

      // Setup app state listener
      this.setupAppStateListener();

      // Start periodic sync
      this.startPeriodicSync();

      this.isInitialized = true;
      console.log('BackgroundSyncService initialized successfully');
    } catch (error) {
      console.error('Failed to initialize BackgroundSyncService:', error);
      throw error;
    }
  }

  private async loadSyncQueue(): Promise<void> {
    try {
      const queueData = await AsyncStorage.getItem('sync_queue');
      if (queueData) {
        this.syncQueue = JSON.parse(queueData);
        console.log(`Loaded ${this.syncQueue.length} items from sync queue`);
      }
    } catch (error) {
      console.error('Failed to load sync queue:', error);
      this.syncQueue = [];
    }
  }

  private async saveSyncQueue(): Promise<void> {
    try {
      await AsyncStorage.setItem('sync_queue', JSON.stringify(this.syncQueue));
    } catch (error) {
      console.error('Failed to save sync queue:', error);
    }
  }

  private setupNetworkListener(): void {
    NetInfo.addEventListener(state => {
      const wasOffline = !this.isOnline;
      this.isOnline = state.isConnected ?? false;

      if (wasOffline && this.isOnline) {
        console.log('Network reconnected, triggering sync');
        this.syncOnNetworkReconnect();
      }
    });
  }

  private setupAppStateListener(): void {
    AppState.addEventListener('change', (nextAppState: AppStateStatus) => {
      const previousState = this.appState;
      this.appState = nextAppState;

      if (previousState.match(/inactive|background/) && nextAppState === 'active') {
        console.log('App came to foreground, triggering sync');
        this.syncOnForeground();
      } else if (nextAppState.match(/inactive|background/)) {
        console.log('App went to background, scheduling background sync');
        this.scheduleBackgroundSync();
      }
    });
  }

  private startPeriodicSync(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
    }

    this.syncTimer = setInterval(() => {
      if (this.appState === 'active' && this.isOnline) {
        this.processSyncQueue();
      }
    }, this.config.syncInterval);
  }

  private stopPeriodicSync(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
  }

  // Public methods

  async addToSyncQueue(
    type: SyncData['type'],
    data: any,
    priority: SyncData['priority'] = 'normal'
  ): Promise<void> {
    const syncItem: SyncData = {
      id: `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      data,
      timestamp: Date.now(),
      retryCount: 0,
      priority,
    };

    this.syncQueue.push(syncItem);
    await this.saveSyncQueue();

    console.log(`Added ${type} to sync queue with priority ${priority}`);

    // If high priority and online, sync immediately
    if (priority === 'high' && this.isOnline && !this.isSyncing) {
      this.processSyncQueue();
    }
  }

  async processSyncQueue(): Promise<void> {
    if (this.isSyncing || !this.isOnline || this.syncQueue.length === 0) {
      return;
    }

    this.isSyncing = true;
    console.log(`Processing sync queue with ${this.syncQueue.length} items`);

    try {
      // Sort by priority and timestamp
      const sortedQueue = [...this.syncQueue].sort((a, b) => {
        const priorityOrder = {high: 3, normal: 2, low: 1};
        const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
        if (priorityDiff !== 0) return priorityDiff;
        return a.timestamp - b.timestamp;
      });

      // Process in batches
      const batch = sortedQueue.slice(0, this.config.batchSize);
      const results = await Promise.allSettled(
        batch.map(item => this.syncItem(item))
      );

      // Remove successfully synced items
      const successfulIds = new Set<string>();
      results.forEach((result, index) => {
        if (result.status === 'fulfilled' && result.value) {
          successfulIds.add(batch[index].id);
        }
      });

      this.syncQueue = this.syncQueue.filter(item => !successfulIds.has(item.id));
      await this.saveSyncQueue();

      console.log(`Sync completed: ${successfulIds.size} successful, ${batch.length - successfulIds.size} failed`);
    } catch (error) {
      console.error('Sync queue processing failed:', error);
    } finally {
      this.isSyncing = false;
    }
  }

  private async syncItem(item: SyncData): Promise<boolean> {
    try {
      console.log(`Syncing ${item.type} (attempt ${item.retryCount + 1})`);

      let success = false;

      switch (item.type) {
        case 'practice-session':
          success = await this.syncPracticeSession(item.data);
          break;
        case 'progress-update':
          success = await this.syncProgressUpdate(item.data);
          break;
        case 'user-preferences':
          success = await this.syncUserPreferences(item.data);
          break;
        case 'content-download':
          success = await this.syncContentDownload(item.data);
          break;
        default:
          console.warn(`Unknown sync type: ${item.type}`);
          return false;
      }

      if (!success) {
        item.retryCount++;
        if (item.retryCount >= this.config.maxRetries) {
          console.error(`Max retries exceeded for ${item.type}, removing from queue`);
          return true; // Remove from queue
        }
        
        // Schedule retry with exponential backoff
        setTimeout(() => {
          this.processSyncQueue();
        }, this.config.retryDelay * Math.pow(2, item.retryCount - 1));
      }

      return success;
    } catch (error) {
      console.error(`Failed to sync ${item.type}:`, error);
      return false;
    }
  }

  private async syncPracticeSession(data: any): Promise<boolean> {
    try {
      // TODO: Implement API call to sync practice session
      const response = await fetch('/api/v1/practice/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add auth headers
        },
        body: JSON.stringify(data),
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to sync practice session:', error);
      return false;
    }
  }

  private async syncProgressUpdate(data: any): Promise<boolean> {
    try {
      // TODO: Implement API call to sync progress update
      const response = await fetch('/api/v1/users/progress', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          // Add auth headers
        },
        body: JSON.stringify(data),
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to sync progress update:', error);
      return false;
    }
  }

  private async syncUserPreferences(data: any): Promise<boolean> {
    try {
      // TODO: Implement API call to sync user preferences
      const response = await fetch('/api/v1/users/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          // Add auth headers
        },
        body: JSON.stringify(data),
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to sync user preferences:', error);
      return false;
    }
  }

  private async syncContentDownload(data: any): Promise<boolean> {
    try {
      // TODO: Implement content download logic
      console.log('Syncing content download:', data);
      return true;
    } catch (error) {
      console.error('Failed to sync content download:', error);
      return false;
    }
  }

  // Event handlers

  async syncOnForeground(): Promise<void> {
    if (this.isOnline) {
      await this.processSyncQueue();
    }
  }

  async syncOnNetworkReconnect(): Promise<void> {
    await this.processSyncQueue();
  }

  async scheduleBackgroundSync(): Promise<void> {
    // In a real implementation, you would use a background task library
    // For now, we'll just ensure the queue is saved
    await this.saveSyncQueue();
    console.log('Background sync scheduled (queue saved)');
  }

  // Utility methods

  async clearSyncQueue(): Promise<void> {
    this.syncQueue = [];
    await this.saveSyncQueue();
    console.log('Sync queue cleared');
  }

  getSyncQueueStatus(): {
    totalItems: number;
    highPriority: number;
    normalPriority: number;
    lowPriority: number;
    isSyncing: boolean;
    isOnline: boolean;
  } {
    const highPriority = this.syncQueue.filter(item => item.priority === 'high').length;
    const normalPriority = this.syncQueue.filter(item => item.priority === 'normal').length;
    const lowPriority = this.syncQueue.filter(item => item.priority === 'low').length;

    return {
      totalItems: this.syncQueue.length,
      highPriority,
      normalPriority,
      lowPriority,
      isSyncing: this.isSyncing,
      isOnline: this.isOnline,
    };
  }

  async forceSyncNow(): Promise<void> {
    if (this.isOnline) {
      await this.processSyncQueue();
    } else {
      throw new Error('Cannot sync while offline');
    }
  }

  destroy(): void {
    this.stopPeriodicSync();
    this.isInitialized = false;
  }
}

export const BackgroundSyncService = new BackgroundSyncServiceClass();