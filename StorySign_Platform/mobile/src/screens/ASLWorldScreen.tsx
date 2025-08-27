import React, {useState} from 'react';
import {View, Text, StyleSheet, TouchableOpacity, Alert} from 'react-native';
import {MobileVideoPlayer} from '../components/MobileVideoPlayer';
import {TouchOptimizedControls} from '../components/TouchOptimizedControls';
import {useDevice} from '../contexts/DeviceContext';
import {useHapticFeedback} from '../hooks/useHapticFeedback';

export const ASLWorldScreen: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [currentStory, setCurrentStory] = useState<string | null>(null);
  const {deviceInfo, checkCapability} = useDevice();
  const {patterns} = useHapticFeedback();

  const handleStartPractice = () => {
    if (!checkCapability('hasCamera')) {
      Alert.alert(
        'Camera Required',
        'ASL practice requires camera access for gesture detection.',
        [{text: 'OK'}]
      );
      return;
    }

    patterns.buttonPress();
    setIsRecording(true);
    // TODO: Start practice session
  };

  const handleStopPractice = () => {
    patterns.buttonPress();
    setIsRecording(false);
    // TODO: Stop practice session
  };

  const handleFrameCapture = (frameData: any) => {
    // TODO: Process frame for gesture detection
    console.log('Frame captured for processing');
  };

  const handleGestureDetected = (gesture: any) => {
    patterns.gestureRecognized();
    // TODO: Handle detected gesture
    console.log('Gesture detected:', gesture);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>ASL World</Text>
        <Text style={styles.subtitle}>
          {isRecording ? 'Practice in progress...' : 'Ready to practice'}
        </Text>
      </View>

      <View style={styles.videoContainer}>
        <MobileVideoPlayer
          onFrameCapture={handleFrameCapture}
          onGestureDetected={handleGestureDetected}
          isRecording={isRecording}
          quality={deviceInfo.networkInfo.isWiFi ? 'high' : 'medium'}
          enableGestureDetection={true}
        />
      </View>

      <View style={styles.controlsContainer}>
        <TouchOptimizedControls
          onPlayPause={isRecording ? handleStopPractice : handleStartPractice}
          isPlaying={isRecording}
          disabled={!checkCapability('hasCamera')}
        />
      </View>

      <View style={styles.statusContainer}>
        <Text style={styles.statusText}>
          Camera: {checkCapability('hasCamera') ? '✅' : '❌'}
        </Text>
        <Text style={styles.statusText}>
          Network: {deviceInfo.networkInfo.isConnected ? '✅' : '❌'}
        </Text>
        <Text style={styles.statusText}>
          Gesture Detection: {isRecording ? '🟢 Active' : '⚪ Inactive'}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  header: {
    padding: 20,
    backgroundColor: '#007AFF',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.9,
  },
  videoContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  controlsContainer: {
    padding: 20,
  },
  statusContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    textAlign: 'center',
  },
});