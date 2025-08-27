import {useCallback} from 'react';
import {Platform, Vibration} from 'react-native';
import ReactNativeHapticFeedback from 'react-native-haptic-feedback';

type HapticType = 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error' | 'selection';

interface HapticOptions {
  enableVibrateFallback?: boolean;
  ignoreAndroidSystemSettings?: boolean;
}

export const useHapticFeedback = () => {
  const triggerHaptic = useCallback((
    type: HapticType = 'light',
    options: HapticOptions = {}
  ) => {
    const {
      enableVibrateFallback = true,
      ignoreAndroidSystemSettings = false,
    } = options;

    try {
      if (Platform.OS === 'ios') {
        // iOS Haptic Feedback
        const hapticOptions = {
          enableVibrateFallback,
          ignoreAndroidSystemSettings: false,
        };

        switch (type) {
          case 'light':
            ReactNativeHapticFeedback.trigger('impactLight', hapticOptions);
            break;
          case 'medium':
            ReactNativeHapticFeedback.trigger('impactMedium', hapticOptions);
            break;
          case 'heavy':
            ReactNativeHapticFeedback.trigger('impactHeavy', hapticOptions);
            break;
          case 'success':
            ReactNativeHapticFeedback.trigger('notificationSuccess', hapticOptions);
            break;
          case 'warning':
            ReactNativeHapticFeedback.trigger('notificationWarning', hapticOptions);
            break;
          case 'error':
            ReactNativeHapticFeedback.trigger('notificationError', hapticOptions);
            break;
          case 'selection':
            ReactNativeHapticFeedback.trigger('selection', hapticOptions);
            break;
          default:
            ReactNativeHapticFeedback.trigger('impactLight', hapticOptions);
        }
      } else if (Platform.OS === 'android') {
        // Android Haptic Feedback
        const hapticOptions = {
          enableVibrateFallback,
          ignoreAndroidSystemSettings,
        };

        // Android has limited haptic feedback types
        switch (type) {
          case 'light':
          case 'selection':
            ReactNativeHapticFeedback.trigger('keyboardPress', hapticOptions);
            break;
          case 'medium':
            ReactNativeHapticFeedback.trigger('keyboardTap', hapticOptions);
            break;
          case 'heavy':
          case 'success':
          case 'warning':
          case 'error':
            ReactNativeHapticFeedback.trigger('longPress', hapticOptions);
            break;
          default:
            ReactNativeHapticFeedback.trigger('keyboardPress', hapticOptions);
        }
      }
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
      
      // Fallback to vibration if haptic feedback fails
      if (enableVibrateFallback) {
        fallbackVibration(type);
      }
    }
  }, []);

  const fallbackVibration = useCallback((type: HapticType) => {
    try {
      switch (type) {
        case 'light':
        case 'selection':
          Vibration.vibrate(10);
          break;
        case 'medium':
          Vibration.vibrate(25);
          break;
        case 'heavy':
          Vibration.vibrate(50);
          break;
        case 'success':
          Vibration.vibrate([0, 50, 50, 50]);
          break;
        case 'warning':
          Vibration.vibrate([0, 100, 50, 100]);
          break;
        case 'error':
          Vibration.vibrate([0, 100, 50, 100, 50, 100]);
          break;
        default:
          Vibration.vibrate(10);
      }
    } catch (error) {
      console.warn('Vibration fallback failed:', error);
    }
  }, []);

  const triggerCustomPattern = useCallback((pattern: number[]) => {
    try {
      Vibration.vibrate(pattern);
    } catch (error) {
      console.warn('Custom vibration pattern failed:', error);
    }
  }, []);

  const cancelVibration = useCallback(() => {
    try {
      Vibration.cancel();
    } catch (error) {
      console.warn('Cancel vibration failed:', error);
    }
  }, []);

  // Predefined patterns for common interactions
  const patterns = {
    buttonPress: () => triggerHaptic('light'),
    buttonLongPress: () => triggerHaptic('medium'),
    swipeAction: () => triggerHaptic('light'),
    pullToRefresh: () => triggerHaptic('medium'),
    errorOccurred: () => triggerHaptic('error'),
    successAction: () => triggerHaptic('success'),
    warningAlert: () => triggerHaptic('warning'),
    menuSelection: () => triggerHaptic('selection'),
    gestureRecognized: () => triggerHaptic('light'),
    practiceComplete: () => triggerCustomPattern([0, 100, 50, 100, 50, 200]),
    milestoneReached: () => triggerCustomPattern([0, 200, 100, 200, 100, 300]),
    incorrectGesture: () => triggerCustomPattern([0, 50, 25, 50]),
    correctGesture: () => triggerCustomPattern([0, 75]),
  };

  return {
    triggerHaptic,
    triggerCustomPattern,
    cancelVibration,
    patterns,
  };
};