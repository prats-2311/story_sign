import React, {useState, useEffect, useRef} from 'react';
import {
  View,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  Text,
  Alert,
  Platform,
} from 'react-native';
import {Camera, useCameraDevices} from 'react-native-vision-camera';
import {useDeviceOrientation} from '../hooks/useDeviceOrientation';
import {useResponsive} from '../hooks/useResponsive';

interface MobileVideoPlayerProps {
  onFrameCapture?: (frameData: any) => void;
  onGestureDetected?: (gesture: any) => void;
  isRecording?: boolean;
  quality?: 'low' | 'medium' | 'high';
  enableGestureDetection?: boolean;
}

export const MobileVideoPlayer: React.FC<MobileVideoPlayerProps> = ({
  onFrameCapture,
  onGestureDetected,
  isRecording = false,
  quality = 'medium',
  enableGestureDetection = true,
}) => {
  const [hasPermission, setHasPermission] = useState(false);
  const [isActive, setIsActive] = useState(true);
  const [cameraPosition, setCameraPosition] = useState<'front' | 'back'>('front');
  const [flashMode, setFlashMode] = useState<'off' | 'on' | 'auto'>('off');
  
  const cameraRef = useRef<Camera>(null);
  const devices = useCameraDevices();
  const {orientation, isLandscape} = useDeviceOrientation();
  const {isMobile, windowSize} = useResponsive();

  const device = cameraPosition === 'front' ? devices.front : devices.back;

  useEffect(() => {
    checkCameraPermission();
  }, []);

  useEffect(() => {
    // Handle app state changes
    const handleAppStateChange = (nextAppState: string) => {
      setIsActive(nextAppState === 'active');
    };

    // In a real implementation, you would add the app state listener here
    return () => {
      // Cleanup
    };
  }, []);

  const checkCameraPermission = async () => {
    try {
      const permission = await Camera.requestCameraPermission();
      setHasPermission(permission === 'authorized');
      
      if (permission === 'denied') {
        Alert.alert(
          'Camera Permission Required',
          'StorySign needs camera access to detect ASL gestures. Please enable camera permission in settings.',
          [
            {text: 'Cancel', style: 'cancel'},
            {text: 'Open Settings', onPress: () => {
              // TODO: Open app settings
            }},
          ]
        );
      }
    } catch (error) {
      console.error('Failed to request camera permission:', error);
      setHasPermission(false);
    }
  };

  const handleFrameProcessor = (frame: any) => {
    'worklet';
    
    if (enableGestureDetection && onFrameCapture) {
      // Process frame for gesture detection
      // This would typically involve calling MediaPipe or similar
      onFrameCapture(frame);
    }
  };

  const toggleCameraPosition = () => {
    setCameraPosition(prev => prev === 'front' ? 'back' : 'front');
  };

  const toggleFlash = () => {
    setFlashMode(prev => {
      switch (prev) {
        case 'off': return 'on';
        case 'on': return 'auto';
        case 'auto': return 'off';
        default: return 'off';
      }
    });
  };

  const getVideoResolution = () => {
    const {width, height} = windowSize;
    const aspectRatio = width / height;

    switch (quality) {
      case 'low':
        return {width: 480, height: Math.round(480 / aspectRatio)};
      case 'medium':
        return {width: 720, height: Math.round(720 / aspectRatio)};
      case 'high':
        return {width: 1080, height: Math.round(1080 / aspectRatio)};
      default:
        return {width: 720, height: Math.round(720 / aspectRatio)};
    }
  };

  const getCameraStyle = () => {
    const {width, height} = Dimensions.get('window');
    
    if (isLandscape) {
      return {
        width: height * 0.7,
        height: width * 0.7,
      };
    }
    
    return {
      width: width * 0.9,
      height: height * 0.6,
    };
  };

  if (!hasPermission) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>
          Camera permission is required for gesture detection
        </Text>
        <TouchableOpacity
          style={styles.permissionButton}
          onPress={checkCameraPermission}
        >
          <Text style={styles.permissionButtonText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!device) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>Camera not available</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={[styles.cameraContainer, getCameraStyle()]}>
        <Camera
          ref={cameraRef}
          style={StyleSheet.absoluteFill}
          device={device}
          isActive={isActive}
          frameProcessor={handleFrameProcessor}
          video={true}
          audio={false}
          orientation={orientation}
          torch={flashMode}
          enableZoomGesture={true}
        />
        
        {/* Camera overlay */}
        <View style={styles.overlay}>
          {/* Recording indicator */}
          {isRecording && (
            <View style={styles.recordingIndicator}>
              <View style={styles.recordingDot} />
              <Text style={styles.recordingText}>Recording</Text>
            </View>
          )}
          
          {/* Gesture detection indicator */}
          {enableGestureDetection && (
            <View style={styles.gestureIndicator}>
              <Text style={styles.gestureText}>👋 Gesture Detection Active</Text>
            </View>
          )}
        </View>
      </View>

      {/* Camera controls */}
      <View style={styles.controls}>
        <TouchableOpacity
          style={styles.controlButton}
          onPress={toggleCameraPosition}
        >
          <Text style={styles.controlButtonText}>
            {cameraPosition === 'front' ? '🤳' : '📷'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.controlButton}
          onPress={toggleFlash}
        >
          <Text style={styles.controlButtonText}>
            {flashMode === 'off' ? '🔦' : flashMode === 'on' ? '💡' : '⚡'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.controlButton}
          onPress={() => setIsActive(!isActive)}
        >
          <Text style={styles.controlButtonText}>
            {isActive ? '⏸️' : '▶️'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cameraContainer: {
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'space-between',
    padding: 16,
  },
  recordingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 0, 0, 0.8)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    alignSelf: 'flex-start',
  },
  recordingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#fff',
    marginRight: 8,
  },
  recordingText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  gestureIndicator: {
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    alignSelf: 'center',
  },
  gestureText: {
    color: '#fff',
    fontSize: 12,
    textAlign: 'center',
  },
  controls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    marginTop: 20,
    paddingHorizontal: 40,
    width: '100%',
  },
  controlButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  controlButtonText: {
    fontSize: 24,
  },
  permissionContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  permissionText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
    color: '#666',
  },
  permissionButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  permissionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#ff0000',
  },
});