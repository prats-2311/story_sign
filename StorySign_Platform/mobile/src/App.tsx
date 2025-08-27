import React, {useEffect, useState} from 'react';
import {
  StatusBar,
  StyleSheet,
  Alert,
  Platform,
  AppState,
  AppStateStatus,
} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import {GestureHandlerRootView} from 'react-native-gesture-handler';
import DeviceInfo from 'react-native-device-info';
import NetInfo from '@react-native-netinfo';
import {request, PERMISSIONS, RESULTS} from 'react-native-permissions';

// Services
import {NotificationService} from './services/NotificationService';
import {BackgroundSyncService} from './services/BackgroundSyncService';
import {AuthService} from './services/AuthService';
import {CameraService} from './services/CameraService';

// Navigation
import {AppNavigator} from './navigation/AppNavigator';

// Contexts
import {AppProvider} from './contexts/AppContext';
import {AuthProvider} from './contexts/AuthContext';
import {DeviceProvider} from './contexts/DeviceContext';

// Components
import {LoadingScreen} from './components/LoadingScreen';
import {OfflineIndicator} from './components/OfflineIndicator';

const App: React.FC = () => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [appState, setAppState] = useState<AppStateStatus>(AppState.currentState);

  useEffect(() => {
    initializeApp();
    setupAppStateListener();
    setupNetworkListener();
    
    return () => {
      // Cleanup listeners
    };
  }, []);

  const initializeApp = async () => {
    try {
      // Initialize device info
      const deviceInfo = {
        deviceId: await DeviceInfo.getUniqueId(),
        deviceType: await DeviceInfo.getDeviceType(),
        systemVersion: DeviceInfo.getSystemVersion(),
        appVersion: DeviceInfo.getVersion(),
        buildNumber: DeviceInfo.getBuildNumber(),
        isTablet: await DeviceInfo.isTablet(),
        hasNotch: await DeviceInfo.hasNotch(),
        supportedAbis: await DeviceInfo.supportedAbis(),
      };

      console.log('Device Info:', deviceInfo);

      // Request permissions
      await requestPermissions();

      // Initialize services
      await NotificationService.initialize();
      await BackgroundSyncService.initialize();
      await AuthService.initialize();
      await CameraService.initialize();

      setIsInitialized(true);
    } catch (error) {
      console.error('App initialization failed:', error);
      Alert.alert(
        'Initialization Error',
        'Failed to initialize the app. Please restart the application.',
        [{text: 'OK'}]
      );
    }
  };

  const requestPermissions = async () => {
    const permissions = Platform.select({
      ios: [
        PERMISSIONS.IOS.CAMERA,
        PERMISSIONS.IOS.MICROPHONE,
        PERMISSIONS.IOS.PHOTO_LIBRARY,
      ],
      android: [
        PERMISSIONS.ANDROID.CAMERA,
        PERMISSIONS.ANDROID.RECORD_AUDIO,
        PERMISSIONS.ANDROID.READ_EXTERNAL_STORAGE,
        PERMISSIONS.ANDROID.WRITE_EXTERNAL_STORAGE,
        PERMISSIONS.ANDROID.POST_NOTIFICATIONS,
      ],
    });

    if (permissions) {
      for (const permission of permissions) {
        try {
          const result = await request(permission);
          console.log(`Permission ${permission}: ${result}`);
          
          if (result === RESULTS.DENIED || result === RESULTS.BLOCKED) {
            console.warn(`Permission ${permission} was denied`);
          }
        } catch (error) {
          console.error(`Error requesting permission ${permission}:`, error);
        }
      }
    }
  };

  const setupAppStateListener = () => {
    const handleAppStateChange = (nextAppState: AppStateStatus) => {
      if (appState.match(/inactive|background/) && nextAppState === 'active') {
        // App has come to the foreground
        BackgroundSyncService.syncOnForeground();
      } else if (nextAppState.match(/inactive|background/)) {
        // App has gone to the background
        BackgroundSyncService.scheduleBackgroundSync();
      }
      
      setAppState(nextAppState);
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription?.remove();
  };

  const setupNetworkListener = () => {
    const unsubscribe = NetInfo.addEventListener(state => {
      setIsOnline(state.isConnected ?? false);
      
      if (state.isConnected) {
        // Network is back, trigger sync
        BackgroundSyncService.syncOnNetworkReconnect();
      }
    });

    return unsubscribe;
  };

  if (!isInitialized) {
    return <LoadingScreen />;
  }

  return (
    <GestureHandlerRootView style={styles.container}>
      <SafeAreaProvider>
        <StatusBar
          barStyle="dark-content"
          backgroundColor="#ffffff"
          translucent={false}
        />
        
        <AppProvider>
          <AuthProvider>
            <DeviceProvider>
              <NavigationContainer>
                <AppNavigator />
                {!isOnline && <OfflineIndicator />}
              </NavigationContainer>
            </DeviceProvider>
          </AuthProvider>
        </AppProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});

export default App;