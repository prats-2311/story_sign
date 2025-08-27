import React, {createContext, useContext, useState, useEffect, ReactNode} from 'react';
import {Platform, Dimensions} from 'react-native';
import DeviceInfo from 'react-native-device-info';
import NetInfo from '@react-native-netinfo';
import Orientation from 'react-native-orientation-locker';

interface DeviceCapabilities {
  hasCamera: boolean;
  hasMicrophone: boolean;
  hasGyroscope: boolean;
  hasAccelerometer: boolean;
  hasBiometrics: boolean;
  hasNFC: boolean;
  supportsHaptics: boolean;
  supportsNotifications: boolean;
}

interface NetworkInfo {
  isConnected: boolean;
  type: string;
  isWiFi: boolean;
  isCellular: boolean;
  strength: number | null;
}

interface DeviceInfo {
  deviceId: string;
  deviceType: 'phone' | 'tablet' | 'unknown';
  platform: 'ios' | 'android';
  systemVersion: string;
  appVersion: string;
  buildNumber: string;
  isTablet: boolean;
  hasNotch: boolean;
  screenDimensions: {width: number; height: number};
  orientation: 'portrait' | 'landscape';
  capabilities: DeviceCapabilities;
  networkInfo: NetworkInfo;
}

interface DeviceContextType {
  deviceInfo: DeviceInfo;
  isOnline: boolean;
  orientation: 'portrait' | 'landscape';
  screenDimensions: {width: number; height: number};
  refreshDeviceInfo: () => Promise<void>;
  checkCapability: (capability: keyof DeviceCapabilities) => boolean;
  getNetworkQuality: () => 'excellent' | 'good' | 'fair' | 'poor' | 'offline';
}

const DeviceContext = createContext<DeviceContextType | undefined>(undefined);

interface DeviceProviderProps {
  children: ReactNode;
}

export const DeviceProvider: React.FC<DeviceProviderProps> = ({children}) => {
  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo>({
    deviceId: '',
    deviceType: 'unknown',
    platform: Platform.OS as 'ios' | 'android',
    systemVersion: '',
    appVersion: '',
    buildNumber: '',
    isTablet: false,
    hasNotch: false,
    screenDimensions: Dimensions.get('window'),
    orientation: 'portrait',
    capabilities: {
      hasCamera: false,
      hasMicrophone: false,
      hasGyroscope: false,
      hasAccelerometer: false,
      hasBiometrics: false,
      hasNFC: false,
      supportsHaptics: false,
      supportsNotifications: false,
    },
    networkInfo: {
      isConnected: false,
      type: 'unknown',
      isWiFi: false,
      isCellular: false,
      strength: null,
    },
  });

  const [isOnline, setIsOnline] = useState(true);
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait');
  const [screenDimensions, setScreenDimensions] = useState(Dimensions.get('window'));

  useEffect(() => {
    initializeDeviceInfo();
    setupListeners();

    return () => {
      // Cleanup listeners
    };
  }, []);

  const initializeDeviceInfo = async () => {
    try {
      const [
        deviceId,
        deviceType,
        systemVersion,
        appVersion,
        buildNumber,
        isTablet,
        hasNotch,
      ] = await Promise.all([
        DeviceInfo.getUniqueId(),
        DeviceInfo.getDeviceType(),
        DeviceInfo.getSystemVersion(),
        DeviceInfo.getVersion(),
        DeviceInfo.getBuildNumber(),
        DeviceInfo.isTablet(),
        DeviceInfo.hasNotch(),
      ]);

      const capabilities = await checkDeviceCapabilities();
      const networkInfo = await getNetworkInfo();

      setDeviceInfo(prev => ({
        ...prev,
        deviceId,
        deviceType: deviceType as 'phone' | 'tablet',
        systemVersion,
        appVersion,
        buildNumber,
        isTablet,
        hasNotch,
        capabilities,
        networkInfo,
      }));
    } catch (error) {
      console.error('Failed to initialize device info:', error);
    }
  };

  const checkDeviceCapabilities = async (): Promise<DeviceCapabilities> => {
    try {
      const [
        hasCamera,
        hasMicrophone,
        hasGyroscope,
        hasAccelerometer,
        hasBiometrics,
        hasNFC,
      ] = await Promise.all([
        DeviceInfo.hasSystemFeature('android.hardware.camera') || Platform.OS === 'ios',
        DeviceInfo.hasSystemFeature('android.hardware.microphone') || Platform.OS === 'ios',
        DeviceInfo.hasSystemFeature('android.hardware.sensor.gyroscope') || Platform.OS === 'ios',
        DeviceInfo.hasSystemFeature('android.hardware.sensor.accelerometer') || Platform.OS === 'ios',
        DeviceInfo.isBatteryCharging(), // Placeholder - would use biometric library
        DeviceInfo.hasSystemFeature('android.hardware.nfc') || false,
      ]);

      return {
        hasCamera,
        hasMicrophone,
        hasGyroscope,
        hasAccelerometer,
        hasBiometrics,
        hasNFC,
        supportsHaptics: Platform.OS === 'ios' || Platform.Version >= 26,
        supportsNotifications: true,
      };
    } catch (error) {
      console.error('Failed to check device capabilities:', error);
      return {
        hasCamera: false,
        hasMicrophone: false,
        hasGyroscope: false,
        hasAccelerometer: false,
        hasBiometrics: false,
        hasNFC: false,
        supportsHaptics: false,
        supportsNotifications: false,
      };
    }
  };

  const getNetworkInfo = async (): Promise<NetworkInfo> => {
    try {
      const netInfo = await NetInfo.fetch();
      
      return {
        isConnected: netInfo.isConnected ?? false,
        type: netInfo.type,
        isWiFi: netInfo.type === 'wifi',
        isCellular: netInfo.type === 'cellular',
        strength: netInfo.details?.strength ?? null,
      };
    } catch (error) {
      console.error('Failed to get network info:', error);
      return {
        isConnected: false,
        type: 'unknown',
        isWiFi: false,
        isCellular: false,
        strength: null,
      };
    }
  };

  const setupListeners = () => {
    // Network listener
    const unsubscribeNetInfo = NetInfo.addEventListener(state => {
      setIsOnline(state.isConnected ?? false);
      
      setDeviceInfo(prev => ({
        ...prev,
        networkInfo: {
          isConnected: state.isConnected ?? false,
          type: state.type,
          isWiFi: state.type === 'wifi',
          isCellular: state.type === 'cellular',
          strength: state.details?.strength ?? null,
        },
      }));
    });

    // Orientation listener
    const handleOrientationChange = (orientation: string) => {
      const newOrientation = orientation.includes('LANDSCAPE') ? 'landscape' : 'portrait';
      setOrientation(newOrientation);
      
      setDeviceInfo(prev => ({
        ...prev,
        orientation: newOrientation,
      }));
    };

    Orientation.addOrientationListener(handleOrientationChange);

    // Dimensions listener
    const dimensionsSubscription = Dimensions.addEventListener('change', ({window}) => {
      setScreenDimensions(window);
      
      setDeviceInfo(prev => ({
        ...prev,
        screenDimensions: window,
      }));
    });

    return () => {
      unsubscribeNetInfo();
      Orientation.removeOrientationListener(handleOrientationChange);
      dimensionsSubscription?.remove();
    };
  };

  const refreshDeviceInfo = async () => {
    await initializeDeviceInfo();
  };

  const checkCapability = (capability: keyof DeviceCapabilities): boolean => {
    return deviceInfo.capabilities[capability];
  };

  const getNetworkQuality = (): 'excellent' | 'good' | 'fair' | 'poor' | 'offline' => {
    if (!isOnline) return 'offline';
    
    const {networkInfo} = deviceInfo;
    
    if (networkInfo.isWiFi) {
      if (networkInfo.strength === null) return 'good';
      if (networkInfo.strength > 80) return 'excellent';
      if (networkInfo.strength > 60) return 'good';
      if (networkInfo.strength > 40) return 'fair';
      return 'poor';
    }
    
    if (networkInfo.isCellular) {
      if (networkInfo.strength === null) return 'fair';
      if (networkInfo.strength > 75) return 'good';
      if (networkInfo.strength > 50) return 'fair';
      return 'poor';
    }
    
    return 'fair';
  };

  const contextValue: DeviceContextType = {
    deviceInfo,
    isOnline,
    orientation,
    screenDimensions,
    refreshDeviceInfo,
    checkCapability,
    getNetworkQuality,
  };

  return (
    <DeviceContext.Provider value={contextValue}>
      {children}
    </DeviceContext.Provider>
  );
};

export const useDevice = (): DeviceContextType => {
  const context = useContext(DeviceContext);
  if (!context) {
    throw new Error('useDevice must be used within a DeviceProvider');
  }
  return context;
};