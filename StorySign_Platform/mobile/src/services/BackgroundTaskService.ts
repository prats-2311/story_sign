import {AppRegistry, AppState} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {BackgroundSyncService} from './BackgroundSyncService';

// Background task handler
const BackgroundTaskHandler = async () => {
  console.log('Background task started');
  
  try {
    // Perform background sync
    await BackgroundSyncService.processSyncQueue();
    
    // Update last background sync timestamp
    await AsyncStorage.setItem('last_background_sync', Date.now().toString());
    
    console.log('Background task completed successfully');
  } catch (error) {
    console.error('Background task failed:', error);
  }
};

// Register background task
AppRegistry.registerHeadlessTask('BackgroundSync', () => BackgroundTaskHandler);

export {BackgroundTaskHandler};