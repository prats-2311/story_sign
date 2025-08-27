import React, {useState} from 'react';
import {
  View,
  TouchableOpacity,
  Text,
  StyleSheet,
  Animated,
  PanGestureHandler,
  State,
  GestureHandlerRootView,
} from 'react-native';
import {useHapticFeedback} from '../hooks/useHapticFeedback';
import {useResponsive} from '../hooks/useResponsive';

interface TouchOptimizedControlsProps {
  onPlayPause?: () => void;
  onNext?: () => void;
  onPrevious?: () => void;
  onSpeedChange?: (speed: number) => void;
  onVolumeChange?: (volume: number) => void;
  isPlaying?: boolean;
  currentSpeed?: number;
  currentVolume?: number;
  disabled?: boolean;
}

export const TouchOptimizedControls: React.FC<TouchOptimizedControlsProps> = ({
  onPlayPause,
  onNext,
  onPrevious,
  onSpeedChange,
  onVolumeChange,
  isPlaying = false,
  currentSpeed = 1.0,
  currentVolume = 0.8,
  disabled = false,
}) => {
  const [showSpeedControl, setShowSpeedControl] = useState(false);
  const [showVolumeControl, setShowVolumeControl] = useState(false);
  const {triggerHaptic} = useHapticFeedback();
  const {isMobile, getResponsiveSpacing} = useResponsive();

  const speedAnimation = new Animated.Value(0);
  const volumeAnimation = new Animated.Value(0);

  const handlePlayPause = () => {
    if (disabled) return;
    triggerHaptic('light');
    onPlayPause?.();
  };

  const handleNext = () => {
    if (disabled) return;
    triggerHaptic('medium');
    onNext?.();
  };

  const handlePrevious = () => {
    if (disabled) return;
    triggerHaptic('medium');
    onPrevious?.();
  };

  const toggleSpeedControl = () => {
    if (disabled) return;
    triggerHaptic('light');
    
    const toValue = showSpeedControl ? 0 : 1;
    setShowSpeedControl(!showSpeedControl);
    
    Animated.spring(speedAnimation, {
      toValue,
      useNativeDriver: true,
      tension: 100,
      friction: 8,
    }).start();
  };

  const toggleVolumeControl = () => {
    if (disabled) return;
    triggerHaptic('light');
    
    const toValue = showVolumeControl ? 0 : 1;
    setShowVolumeControl(!showVolumeControl);
    
    Animated.spring(volumeAnimation, {
      toValue,
      useNativeDriver: true,
      tension: 100,
      friction: 8,
    }).start();
  };

  const handleSpeedSelect = (speed: number) => {
    triggerHaptic('medium');
    onSpeedChange?.(speed);
    toggleSpeedControl();
  };

  const handleVolumeGesture = (event: any) => {
    if (event.nativeEvent.state === State.ACTIVE) {
      const volume = Math.max(0, Math.min(1, event.nativeEvent.translationY / -200 + currentVolume));
      onVolumeChange?.(volume);
    }
  };

  const speedOptions = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];

  const getButtonSize = () => {
    return isMobile ? 60 : 50;
  };

  const getIconSize = () => {
    return isMobile ? 24 : 20;
  };

  return (
    <GestureHandlerRootView style={styles.container}>
      <View style={[styles.controlsContainer, {padding: getResponsiveSpacing()}]}>
        
        {/* Main playback controls */}
        <View style={styles.mainControls}>
          <TouchableOpacity
            style={[
              styles.controlButton,
              {width: getButtonSize(), height: getButtonSize()},
              disabled && styles.disabledButton,
            ]}
            onPress={handlePrevious}
            disabled={disabled}
            activeOpacity={0.7}
          >
            <Text style={[styles.buttonIcon, {fontSize: getIconSize()}]}>⏮️</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.playButton,
              {width: getButtonSize() + 20, height: getButtonSize() + 20},
              disabled && styles.disabledButton,
            ]}
            onPress={handlePlayPause}
            disabled={disabled}
            activeOpacity={0.7}
          >
            <Text style={[styles.playIcon, {fontSize: getIconSize() + 8}]}>
              {isPlaying ? '⏸️' : '▶️'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.controlButton,
              {width: getButtonSize(), height: getButtonSize()},
              disabled && styles.disabledButton,
            ]}
            onPress={handleNext}
            disabled={disabled}
            activeOpacity={0.7}
          >
            <Text style={[styles.buttonIcon, {fontSize: getIconSize()}]}>⏭️</Text>
          </TouchableOpacity>
        </View>

        {/* Secondary controls */}
        <View style={styles.secondaryControls}>
          <TouchableOpacity
            style={[
              styles.secondaryButton,
              disabled && styles.disabledButton,
            ]}
            onPress={toggleSpeedControl}
            disabled={disabled}
            activeOpacity={0.7}
          >
            <Text style={styles.secondaryButtonText}>{currentSpeed}x</Text>
          </TouchableOpacity>

          <PanGestureHandler onGestureEvent={handleVolumeGesture}>
            <Animated.View>
              <TouchableOpacity
                style={[
                  styles.secondaryButton,
                  disabled && styles.disabledButton,
                ]}
                onPress={toggleVolumeControl}
                disabled={disabled}
                activeOpacity={0.7}
              >
                <Text style={styles.secondaryButtonText}>
                  {currentVolume > 0.5 ? '🔊' : currentVolume > 0 ? '🔉' : '🔇'}
                </Text>
              </TouchableOpacity>
            </Animated.View>
          </PanGestureHandler>
        </View>

        {/* Speed control overlay */}
        {showSpeedControl && (
          <Animated.View
            style={[
              styles.speedOverlay,
              {
                opacity: speedAnimation,
                transform: [
                  {
                    scale: speedAnimation.interpolate({
                      inputRange: [0, 1],
                      outputRange: [0.8, 1],
                    }),
                  },
                ],
              },
            ]}
          >
            <Text style={styles.overlayTitle}>Playback Speed</Text>
            <View style={styles.speedOptions}>
              {speedOptions.map((speed) => (
                <TouchableOpacity
                  key={speed}
                  style={[
                    styles.speedOption,
                    currentSpeed === speed && styles.selectedSpeedOption,
                  ]}
                  onPress={() => handleSpeedSelect(speed)}
                >
                  <Text
                    style={[
                      styles.speedOptionText,
                      currentSpeed === speed && styles.selectedSpeedOptionText,
                    ]}
                  >
                    {speed}x
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </Animated.View>
        )}

        {/* Volume control overlay */}
        {showVolumeControl && (
          <Animated.View
            style={[
              styles.volumeOverlay,
              {
                opacity: volumeAnimation,
                transform: [
                  {
                    scale: volumeAnimation.interpolate({
                      inputRange: [0, 1],
                      outputRange: [0.8, 1],
                    }),
                  },
                ],
              },
            ]}
          >
            <Text style={styles.overlayTitle}>Volume</Text>
            <View style={styles.volumeSlider}>
              <View style={styles.volumeTrack}>
                <View
                  style={[
                    styles.volumeFill,
                    {width: `${currentVolume * 100}%`},
                  ]}
                />
              </View>
              <Text style={styles.volumeText}>
                {Math.round(currentVolume * 100)}%
              </Text>
            </View>
          </Animated.View>
        )}
      </View>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  controlsContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    borderRadius: 16,
    margin: 16,
  },
  mainControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  controlButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 8,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  playButton: {
    backgroundColor: '#007AFF',
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 16,
    shadowColor: '#007AFF',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  buttonIcon: {
    color: '#fff',
  },
  playIcon: {
    color: '#fff',
  },
  secondaryControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginHorizontal: 8,
    minWidth: 60,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  disabledButton: {
    opacity: 0.5,
  },
  speedOverlay: {
    position: 'absolute',
    top: -120,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    borderRadius: 12,
    padding: 16,
  },
  volumeOverlay: {
    position: 'absolute',
    top: -100,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    borderRadius: 12,
    padding: 16,
  },
  overlayTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 12,
  },
  speedOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  speedOption: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    margin: 4,
  },
  selectedSpeedOption: {
    backgroundColor: '#007AFF',
  },
  speedOptionText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  selectedSpeedOptionText: {
    color: '#fff',
  },
  volumeSlider: {
    alignItems: 'center',
  },
  volumeTrack: {
    width: '80%',
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 2,
    marginBottom: 8,
  },
  volumeFill: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 2,
  },
  volumeText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
});