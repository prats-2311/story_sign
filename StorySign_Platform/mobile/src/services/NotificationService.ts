import PushNotification, {Importance} from 'react-native-push-notification';
import messaging from '@react-native-firebase/messaging';
import {Platform, PermissionsAndroid} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface NotificationData {
  title: string;
  message: string;
  data?: any;
  channelId?: string;
  priority?: 'high' | 'normal' | 'low';
  sound?: boolean;
  vibrate?: boolean;
}

class NotificationServiceClass {
  private isInitialized = false;
  private fcmToken: string | null = null;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Request permission for notifications
      await this.requestPermission();

      // Configure push notifications
      this.configurePushNotifications();

      // Initialize Firebase messaging
      await this.initializeFirebaseMessaging();

      this.isInitialized = true;
      console.log('NotificationService initialized successfully');
    } catch (error) {
      console.error('Failed to initialize NotificationService:', error);
      throw error;
    }
  }

  private async requestPermission(): Promise<boolean> {
    if (Platform.OS === 'android') {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS,
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    } else {
      const authStatus = await messaging().requestPermission();
      const enabled =
        authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
        authStatus === messaging.AuthorizationStatus.PROVISIONAL;
      return enabled;
    }
  }

  private configurePushNotifications(): void {
    PushNotification.configure({
      onRegister: (token) => {
        console.log('Push notification token:', token);
        this.storePushToken(token.token);
      },

      onNotification: (notification) => {
        console.log('Notification received:', notification);
        this.handleNotificationReceived(notification);
      },

      onAction: (notification) => {
        console.log('Notification action:', notification);
        this.handleNotificationAction(notification);
      },

      onRegistrationError: (err) => {
        console.error('Push notification registration error:', err);
      },

      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },

      popInitialNotification: true,
      requestPermissions: Platform.OS === 'ios',
    });

    // Create notification channels for Android
    if (Platform.OS === 'android') {
      this.createNotificationChannels();
    }
  }

  private createNotificationChannels(): void {
    const channels = [
      {
        channelId: 'practice-reminders',
        channelName: 'Practice Reminders',
        channelDescription: 'Reminders for ASL practice sessions',
        importance: Importance.HIGH,
        vibrate: true,
      },
      {
        channelId: 'progress-updates',
        channelName: 'Progress Updates',
        channelDescription: 'Updates about learning progress',
        importance: Importance.DEFAULT,
        vibrate: false,
      },
      {
        channelId: 'social-notifications',
        channelName: 'Social Notifications',
        channelDescription: 'Friend requests and group activities',
        importance: Importance.DEFAULT,
        vibrate: true,
      },
      {
        channelId: 'system-alerts',
        channelName: 'System Alerts',
        channelDescription: 'Important system notifications',
        importance: Importance.HIGH,
        vibrate: true,
      },
    ];

    channels.forEach(channel => {
      PushNotification.createChannel(channel, () => {
        console.log(`Created notification channel: ${channel.channelId}`);
      });
    });
  }

  private async initializeFirebaseMessaging(): Promise<void> {
    try {
      // Get FCM token
      this.fcmToken = await messaging().getToken();
      console.log('FCM Token:', this.fcmToken);
      await this.storeFCMToken(this.fcmToken);

      // Listen for token refresh
      messaging().onTokenRefresh(token => {
        console.log('FCM Token refreshed:', token);
        this.fcmToken = token;
        this.storeFCMToken(token);
      });

      // Handle background messages
      messaging().setBackgroundMessageHandler(async remoteMessage => {
        console.log('Message handled in the background!', remoteMessage);
        await this.handleBackgroundMessage(remoteMessage);
      });

      // Handle foreground messages
      messaging().onMessage(async remoteMessage => {
        console.log('Message received in foreground!', remoteMessage);
        await this.handleForegroundMessage(remoteMessage);
      });

    } catch (error) {
      console.error('Firebase messaging initialization failed:', error);
    }
  }

  private async storePushToken(token: string): Promise<void> {
    try {
      await AsyncStorage.setItem('push_token', token);
    } catch (error) {
      console.error('Failed to store push token:', error);
    }
  }

  private async storeFCMToken(token: string): Promise<void> {
    try {
      await AsyncStorage.setItem('fcm_token', token);
      // TODO: Send token to backend server
    } catch (error) {
      console.error('Failed to store FCM token:', error);
    }
  }

  private handleNotificationReceived(notification: any): void {
    // Handle notification tap
    if (notification.userInteraction) {
      this.navigateToNotificationTarget(notification);
    }
  }

  private handleNotificationAction(notification: any): void {
    // Handle notification actions (buttons, etc.)
    console.log('Notification action handled:', notification);
  }

  private async handleBackgroundMessage(remoteMessage: any): Promise<void> {
    // Process background message
    console.log('Background message processed:', remoteMessage);
  }

  private async handleForegroundMessage(remoteMessage: any): Promise<void> {
    // Show local notification for foreground messages
    this.showLocalNotification({
      title: remoteMessage.notification?.title || 'StorySign',
      message: remoteMessage.notification?.body || 'New notification',
      data: remoteMessage.data,
    });
  }

  private navigateToNotificationTarget(notification: any): void {
    // TODO: Implement navigation based on notification data
    console.log('Navigate to notification target:', notification);
  }

  // Public methods

  async showLocalNotification(data: NotificationData): Promise<void> {
    PushNotification.localNotification({
      title: data.title,
      message: data.message,
      channelId: data.channelId || 'system-alerts',
      priority: data.priority || 'normal',
      soundName: data.sound ? 'default' : undefined,
      vibrate: data.vibrate !== false,
      userInfo: data.data,
    });
  }

  async schedulePracticeReminder(
    title: string,
    message: string,
    date: Date,
    repeatType?: 'day' | 'week'
  ): Promise<void> {
    PushNotification.localNotificationSchedule({
      title,
      message,
      date,
      channelId: 'practice-reminders',
      repeatType,
      userInfo: {
        type: 'practice-reminder',
      },
    });
  }

  async cancelAllNotifications(): Promise<void> {
    PushNotification.cancelAllLocalNotifications();
  }

  async cancelNotification(id: string): Promise<void> {
    PushNotification.cancelLocalNotifications({id});
  }

  async getFCMToken(): Promise<string | null> {
    return this.fcmToken;
  }

  async getStoredTokens(): Promise<{pushToken?: string; fcmToken?: string}> {
    try {
      const [pushToken, fcmToken] = await Promise.all([
        AsyncStorage.getItem('push_token'),
        AsyncStorage.getItem('fcm_token'),
      ]);

      return {
        pushToken: pushToken || undefined,
        fcmToken: fcmToken || undefined,
      };
    } catch (error) {
      console.error('Failed to get stored tokens:', error);
      return {};
    }
  }

  // Practice session notifications
  async notifyPracticeComplete(score: number, improvement: number): Promise<void> {
    await this.showLocalNotification({
      title: 'Practice Complete! 🎉',
      message: `Great job! You scored ${score}% with ${improvement}% improvement.`,
      channelId: 'progress-updates',
      data: {
        type: 'practice-complete',
        score,
        improvement,
      },
    });
  }

  async notifyMilestoneReached(milestone: string): Promise<void> {
    await this.showLocalNotification({
      title: 'Milestone Reached! 🏆',
      message: `Congratulations! You've reached: ${milestone}`,
      channelId: 'progress-updates',
      data: {
        type: 'milestone',
        milestone,
      },
    });
  }

  async notifyFriendRequest(friendName: string): Promise<void> {
    await this.showLocalNotification({
      title: 'New Friend Request',
      message: `${friendName} wants to connect with you!`,
      channelId: 'social-notifications',
      data: {
        type: 'friend-request',
        friendName,
      },
    });
  }

  async notifyGroupInvitation(groupName: string): Promise<void> {
    await this.showLocalNotification({
      title: 'Group Invitation',
      message: `You've been invited to join "${groupName}"`,
      channelId: 'social-notifications',
      data: {
        type: 'group-invitation',
        groupName,
      },
    });
  }
}

export const NotificationService = new NotificationServiceClass();