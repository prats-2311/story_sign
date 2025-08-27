# StorySign Mobile App

Native mobile application for the StorySign ASL learning platform.

## Features

- **Native Mobile Experience**: Optimized for iOS and Android devices
- **Camera Integration**: Real-time video capture for gesture detection
- **Touch-Optimized Controls**: Mobile-friendly interface with haptic feedback
- **Push Notifications**: Practice reminders and progress updates
- **Background Sync**: Offline capability with automatic data synchronization
- **Device Integration**: Utilizes native device capabilities (camera, microphone, sensors)

## Architecture

### Core Services
- **NotificationService**: Push notifications and local alerts
- **BackgroundSyncService**: Offline data synchronization
- **AuthService**: User authentication and session management
- **CameraService**: Camera permissions and configuration

### Key Components
- **MobileVideoPlayer**: Camera integration with gesture detection
- **TouchOptimizedControls**: Mobile-friendly playback controls
- **DeviceContext**: Device capabilities and network status
- **AppNavigator**: Navigation with tab and stack navigators

### Native Integrations
- Camera and microphone access
- Push notifications (Firebase Cloud Messaging)
- Haptic feedback
- Device orientation handling
- Network status monitoring
- Secure storage (Keychain/Keystore)

## Requirements

### Development Environment
- Node.js 16+
- React Native CLI
- Android Studio (for Android development)
- Xcode (for iOS development)

### Device Requirements
- iOS 12.0+ or Android 6.0+
- Camera access for gesture detection
- Network connectivity for content sync

## Installation

1. **Install Dependencies**
   ```bash
   cd mobile
   npm install
   ```

2. **iOS Setup**
   ```bash
   cd ios
   pod install
   cd ..
   ```

3. **Android Setup**
   - Ensure Android SDK is installed
   - Configure signing certificates

## Running the App

### Development
```bash
# Start Metro bundler
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android
```

### Production Builds
```bash
# Build for Android
npm run build:android

# Build for iOS
npm run build:ios
```

## Configuration

### Firebase Setup
1. Add `google-services.json` (Android) and `GoogleService-Info.plist` (iOS)
2. Configure Firebase project for push notifications

### API Configuration
Update API endpoints in service files to match your backend deployment.

### Permissions
The app requires the following permissions:
- Camera (for gesture detection)
- Microphone (for audio features)
- Storage (for offline content)
- Notifications (for practice reminders)

## Features Implementation Status

### ✅ Completed
- Basic app structure and navigation
- Device capability detection
- Camera service integration
- Push notification setup
- Background sync framework
- Touch-optimized controls
- Haptic feedback system

### 🚧 In Progress
- Complete camera integration with MediaPipe
- Full authentication flow
- Story library integration
- Progress tracking
- Offline content management

### 📋 Planned
- Advanced gesture recognition
- Social features
- Group practice sessions
- Analytics integration
- Performance optimizations

## Testing

```bash
# Run unit tests
npm test

# Run integration tests
npm run test:integration

# Run on device
npm run test:device
```

## Deployment

### App Store (iOS)
1. Configure signing certificates
2. Build release version
3. Upload to App Store Connect
4. Submit for review

### Google Play (Android)
1. Generate signed APK/AAB
2. Upload to Google Play Console
3. Configure store listing
4. Submit for review

## Performance Considerations

- **Video Processing**: Optimized for mobile GPUs
- **Battery Usage**: Adaptive quality based on battery level
- **Network Usage**: Bandwidth optimization for cellular connections
- **Memory Management**: Efficient handling of video frames and data

## Security

- Secure token storage using Keychain/Keystore
- Certificate pinning for API communications
- Biometric authentication support
- Data encryption for offline storage

## Troubleshooting

### Common Issues
1. **Camera Permission Denied**: Check device settings
2. **Build Failures**: Ensure all dependencies are installed
3. **Network Issues**: Verify API endpoint configuration
4. **Performance Issues**: Check device capabilities and adjust quality settings

### Debug Tools
- React Native Debugger
- Flipper integration
- Native logging (Xcode/Android Studio)

## Contributing

1. Follow React Native best practices
2. Test on both iOS and Android
3. Ensure accessibility compliance
4. Update documentation for new features

## License

This project is part of the StorySign platform. See main project license for details.