import {useState, useEffect} from 'react';
import {Dimensions} from 'react-native';
import Orientation from 'react-native-orientation-locker';

interface OrientationState {
  orientation: 'portrait' | 'landscape' | 'portrait-upside-down' | 'landscape-left' | 'landscape-right';
  isLandscape: boolean;
  isPortrait: boolean;
  screenDimensions: {width: number; height: number};
  safeOrientation: 'portrait' | 'landscape';
}

export const useDeviceOrientation = () => {
  const [orientationState, setOrientationState] = useState<OrientationState>(() => {
    const {width, height} = Dimensions.get('window');
    const isLandscape = width > height;
    
    return {
      orientation: isLandscape ? 'landscape' : 'portrait',
      isLandscape,
      isPortrait: !isLandscape,
      screenDimensions: {width, height},
      safeOrientation: isLandscape ? 'landscape' : 'portrait',
    };
  });

  useEffect(() => {
    // Get initial orientation
    Orientation.getOrientation((orientation) => {
      updateOrientationState(orientation);
    });

    // Listen for orientation changes
    const handleOrientationChange = (orientation: string) => {
      updateOrientationState(orientation);
    };

    Orientation.addOrientationListener(handleOrientationChange);

    // Listen for dimension changes (fallback)
    const dimensionsSubscription = Dimensions.addEventListener('change', ({window}) => {
      const isLandscape = window.width > window.height;
      const orientation = isLandscape ? 'landscape' : 'portrait';
      
      setOrientationState(prev => ({
        ...prev,
        screenDimensions: window,
        isLandscape,
        isPortrait: !isLandscape,
        safeOrientation: orientation,
      }));
    });

    return () => {
      Orientation.removeOrientationListener(handleOrientationChange);
      dimensionsSubscription?.remove();
    };
  }, []);

  const updateOrientationState = (orientation: string) => {
    const {width, height} = Dimensions.get('window');
    
    let normalizedOrientation: OrientationState['orientation'];
    let isLandscape: boolean;
    
    switch (orientation) {
      case 'PORTRAIT':
      case 'PORTRAIT-UPSIDEDOWN':
        normalizedOrientation = orientation === 'PORTRAIT' ? 'portrait' : 'portrait-upside-down';
        isLandscape = false;
        break;
      case 'LANDSCAPE-LEFT':
        normalizedOrientation = 'landscape-left';
        isLandscape = true;
        break;
      case 'LANDSCAPE-RIGHT':
        normalizedOrientation = 'landscape-right';
        isLandscape = true;
        break;
      default:
        // Fallback to dimension-based detection
        isLandscape = width > height;
        normalizedOrientation = isLandscape ? 'landscape' : 'portrait';
    }

    const safeOrientation = isLandscape ? 'landscape' : 'portrait';

    setOrientationState({
      orientation: normalizedOrientation,
      isLandscape,
      isPortrait: !isLandscape,
      screenDimensions: {width, height},
      safeOrientation,
    });
  };

  // Utility functions
  const lockToPortrait = () => {
    Orientation.lockToPortrait();
  };

  const lockToLandscape = () => {
    Orientation.lockToLandscape();
  };

  const lockToLandscapeLeft = () => {
    Orientation.lockToLandscapeLeft();
  };

  const lockToLandscapeRight = () => {
    Orientation.lockToLandscapeRight();
  };

  const unlockAllOrientations = () => {
    Orientation.unlockAllOrientations();
  };

  const getOrientationSpecificDimensions = () => {
    const {width, height} = orientationState.screenDimensions;
    
    if (orientationState.isLandscape) {
      return {
        width: Math.max(width, height),
        height: Math.min(width, height),
      };
    } else {
      return {
        width: Math.min(width, height),
        height: Math.max(width, height),
      };
    }
  };

  const getAspectRatio = () => {
    const {width, height} = orientationState.screenDimensions;
    return width / height;
  };

  const isTabletSize = () => {
    const {width, height} = orientationState.screenDimensions;
    const minDimension = Math.min(width, height);
    return minDimension >= 768; // iPad mini size threshold
  };

  const getOptimalVideoOrientation = () => {
    // For ASL learning, portrait is often better for full-body gestures
    // Landscape might be better for detailed hand movements
    return orientationState.isLandscape ? 'landscape' : 'portrait';
  };

  const shouldUseCompactLayout = () => {
    const {width, height} = orientationState.screenDimensions;
    const minDimension = Math.min(width, height);
    
    // Use compact layout for small screens or portrait orientation on phones
    return minDimension < 600 || (orientationState.isPortrait && !isTabletSize());
  };

  return {
    ...orientationState,
    lockToPortrait,
    lockToLandscape,
    lockToLandscapeLeft,
    lockToLandscapeRight,
    unlockAllOrientations,
    getOrientationSpecificDimensions,
    getAspectRatio,
    isTabletSize: isTabletSize(),
    getOptimalVideoOrientation,
    shouldUseCompactLayout: shouldUseCompactLayout(),
  };
};