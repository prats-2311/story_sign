import {Camera} from 'react-native-vision-camera';
import {Platform} from 'react-native';

interface CameraConfig {
  quality: 'low' | 'medium' | 'high' | 'ultra';
  enableGestureDetection: boolean;
  frameRate: number;
  enableAudio: boolean;
}

class CameraServiceClass {
  private isInitialized = false;
  private hasPermission = false;
  private config: CameraConfig = {
    quality: 'medium',
    enableGestureDetection: true,
    frameRate: 30,
    enableAudio: false,
  };

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Request camera permission
      await this.requestPermissions();
      
      this.isInitialized = true;
      console.log('CameraService initialized successfully');
    } catch (error) {
      console.error('Failed to initialize CameraService:', error);
      throw error;
    }
  }

  private async requestPermissions(): Promise<void> {
    try {
      const cameraPermission = await Camera.requestCameraPermission();
      
      if (cameraPermission === 'authorized') {
        this.hasPermission = true;
      } else {
        this.hasPermission = false;
        throw new Error('Camera permission denied');
      }

      // Request microphone permission if audio is enabled
      if (this.config.enableAudio) {
        const microphonePermission = await Camera.requestMicrophonePermission();
        if (microphonePermission !== 'authorized') {
          console.warn('Microphone permission denied, audio will be disabled');
          this.config.enableAudio = false;
        }
      }
    } catch (error) {
      console.error('Permission request failed:', error);
      throw error;
    }
  }

  async checkPermissions(): Promise<{camera: boolean; microphone: boolean}> {
    try {
      const cameraStatus = await Camera.getCameraPermissionStatus();
      const microphoneStatus = await Camera.getMicrophonePermissionStatus();

      return {
        camera: cameraStatus === 'authorized',
        microphone: microphoneStatus === 'authorized',
      };
    } catch (error) {
      console.error('Permission check failed:', error);
      return {camera: false, microphone: false};
    }
  }

  getConfig(): CameraConfig {
    return {...this.config};
  }

  updateConfig(updates: Partial<CameraConfig>): void {
    this.config = {...this.config, ...updates};
  }

  getOptimalSettings(deviceCapabilities: any) {
    // Adjust settings based on device capabilities
    const settings = {
      ...this.config,
    };

    // Adjust quality based on device performance
    if (deviceCapabilities.isLowEndDevice) {
      settings.quality = 'low';
      settings.frameRate = 15;
    } else if (deviceCapabilities.isMidRangeDevice) {
      settings.quality = 'medium';
      settings.frameRate = 24;
    }

    // Adjust for battery optimization
    if (deviceCapabilities.batteryLevel < 20) {
      settings.quality = 'low';
      settings.frameRate = Math.min(settings.frameRate, 15);
    }

    return settings;
  }

  getVideoResolution(quality: CameraConfig['quality']) {
    switch (quality) {
      case 'low':
        return {width: 480, height: 640};
      case 'medium':
        return {width: 720, height: 1280};
      case 'high':
        return {width: 1080, height: 1920};
      case 'ultra':
        return {width: 1440, height: 2560};
      default:
        return {width: 720, height: 1280};
    }
  }

  hasPermissions(): boolean {
    return this.hasPermission;
  }

  isSupported(): boolean {
    return Platform.OS === 'ios' || Platform.OS === 'android';
  }
}

export const CameraService = new CameraServiceClass();