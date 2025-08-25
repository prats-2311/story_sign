/**
 * Mock Realtime Service
 *
 * Provides a mock implementation of the RealtimeService interface
 * for development and testing purposes.
 */

import {
  RealtimeService,
  MessageHandler,
  ConnectionStatus,
} from "../types/module";

interface ChannelInfo {
  status: ConnectionStatus;
  handlers: MessageHandler[];
  lastMessage?: any;
  messageCount: number;
}

export class MockRealtimeService implements RealtimeService {
  private channels: Map<string, ChannelInfo> = new Map();
  private messageQueue: Array<{
    channel: string;
    message: any;
    timestamp: string;
  }> = [];
  private simulationIntervals: Map<string, NodeJS.Timeout> = new Map();

  constructor() {
    console.log("MockRealtimeService: Initialized");
  }

  async connect(channel: string): Promise<void> {
    console.log(`MockRealtime: Connecting to channel ${channel}...`);

    // Simulate connection delay
    await new Promise((resolve) => setTimeout(resolve, 200));

    const channelInfo: ChannelInfo = {
      status: ConnectionStatus.CONNECTED,
      handlers: [],
      messageCount: 0,
    };

    this.channels.set(channel, channelInfo);

    // Start simulating messages for certain channels
    this.startChannelSimulation(channel);

    console.log(`MockRealtime: Connected to channel ${channel}`);
  }

  async disconnect(channel: string): Promise<void> {
    const channelInfo = this.channels.get(channel);
    if (!channelInfo) {
      console.log(`MockRealtime: Channel ${channel} not found`);
      return;
    }

    console.log(`MockRealtime: Disconnecting from channel ${channel}...`);

    // Stop simulation
    this.stopChannelSimulation(channel);

    // Update status
    channelInfo.status = ConnectionStatus.DISCONNECTED;

    // Clear handlers
    channelInfo.handlers = [];

    console.log(`MockRealtime: Disconnected from channel ${channel}`);
  }

  send(channel: string, message: any): void {
    const channelInfo = this.channels.get(channel);
    if (!channelInfo || channelInfo.status !== ConnectionStatus.CONNECTED) {
      console.warn(
        `MockRealtime: Cannot send to channel ${channel} - not connected`
      );
      return;
    }

    const messageWithMetadata = {
      ...message,
      timestamp: new Date().toISOString(),
      channel,
      messageId: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    };

    console.log(
      `MockRealtime: Sending message to ${channel}:`,
      messageWithMetadata
    );

    // Add to message queue for debugging
    this.messageQueue.push({
      channel,
      message: messageWithMetadata,
      timestamp: messageWithMetadata.timestamp,
    });

    // Simulate message echo (for testing)
    setTimeout(() => {
      this.deliverMessage(channel, {
        type: "echo",
        originalMessage: messageWithMetadata,
        timestamp: new Date().toISOString(),
      });
    }, 50);
  }

  subscribe(channel: string, handler: MessageHandler): void {
    const channelInfo = this.channels.get(channel);
    if (!channelInfo) {
      console.warn(
        `MockRealtime: Cannot subscribe to channel ${channel} - not connected`
      );
      return;
    }

    channelInfo.handlers.push(handler);
    console.log(
      `MockRealtime: Subscribed to channel ${channel} (${channelInfo.handlers.length} handlers)`
    );
  }

  unsubscribe(channel: string, handler: MessageHandler): void {
    const channelInfo = this.channels.get(channel);
    if (!channelInfo) {
      console.log(`MockRealtime: Channel ${channel} not found for unsubscribe`);
      return;
    }

    const index = channelInfo.handlers.indexOf(handler);
    if (index > -1) {
      channelInfo.handlers.splice(index, 1);
      console.log(
        `MockRealtime: Unsubscribed from channel ${channel} (${channelInfo.handlers.length} handlers remaining)`
      );
    }
  }

  getConnectionStatus(channel: string): ConnectionStatus {
    const channelInfo = this.channels.get(channel);
    return channelInfo?.status || ConnectionStatus.DISCONNECTED;
  }

  // Additional methods for testing and development
  public getAllChannels(): Map<string, ChannelInfo> {
    return new Map(this.channels);
  }

  public getMessageQueue(): Array<{
    channel: string;
    message: any;
    timestamp: string;
  }> {
    return [...this.messageQueue];
  }

  public clearMessageQueue(): void {
    this.messageQueue = [];
    console.log("MockRealtime: Message queue cleared");
  }

  public simulateMessage(channel: string, message: any): void {
    this.deliverMessage(channel, {
      ...message,
      timestamp: new Date().toISOString(),
      simulated: true,
    });
  }

  public simulateConnectionError(channel: string): void {
    const channelInfo = this.channels.get(channel);
    if (channelInfo) {
      channelInfo.status = ConnectionStatus.ERROR;
      this.deliverMessage(channel, {
        type: "connection_error",
        error: "Simulated connection error",
        timestamp: new Date().toISOString(),
      });
    }
  }

  public simulateReconnection(channel: string): void {
    const channelInfo = this.channels.get(channel);
    if (channelInfo) {
      channelInfo.status = ConnectionStatus.CONNECTING;

      setTimeout(() => {
        if (channelInfo.status === ConnectionStatus.CONNECTING) {
          channelInfo.status = ConnectionStatus.CONNECTED;
          this.deliverMessage(channel, {
            type: "reconnected",
            timestamp: new Date().toISOString(),
          });
        }
      }, 1000);
    }
  }

  private deliverMessage(channel: string, message: any): void {
    const channelInfo = this.channels.get(channel);
    if (!channelInfo) {
      return;
    }

    channelInfo.lastMessage = message;
    channelInfo.messageCount++;

    // Deliver to all handlers
    channelInfo.handlers.forEach((handler) => {
      try {
        handler(message);
      } catch (error) {
        console.error(
          `MockRealtime: Handler error for channel ${channel}:`,
          error
        );
      }
    });

    console.log(
      `MockRealtime: Delivered message to ${channel} (${channelInfo.handlers.length} handlers)`
    );
  }

  private startChannelSimulation(channel: string): void {
    // Different simulation patterns for different channels
    switch (channel) {
      case "video-processing":
        this.simulateVideoProcessing(channel);
        break;
      case "asl-feedback":
        this.simulateASLFeedback(channel);
        break;
      case "notifications":
        this.simulateNotifications(channel);
        break;
      default:
        // Generic simulation
        this.simulateGenericMessages(channel);
    }
  }

  private stopChannelSimulation(channel: string): void {
    const interval = this.simulationIntervals.get(channel);
    if (interval) {
      clearInterval(interval);
      this.simulationIntervals.delete(channel);
    }
  }

  private simulateVideoProcessing(channel: string): void {
    const interval = setInterval(() => {
      const channelInfo = this.channels.get(channel);
      if (!channelInfo || channelInfo.status !== ConnectionStatus.CONNECTED) {
        return;
      }

      // Simulate processed frame data
      this.deliverMessage(channel, {
        type: "processed_frame",
        frameNumber: Math.floor(Math.random() * 1000),
        landmarks: {
          hands: Math.random() > 0.3 ? this.generateMockLandmarks() : null,
          face: Math.random() > 0.5 ? this.generateMockLandmarks() : null,
          pose: Math.random() > 0.7 ? this.generateMockLandmarks() : null,
        },
        processingTime: Math.floor(Math.random() * 50) + 10,
        confidence: Math.random(),
        timestamp: new Date().toISOString(),
      });
    }, 100); // 10 FPS simulation

    this.simulationIntervals.set(channel, interval);
  }

  private simulateASLFeedback(channel: string): void {
    const interval = setInterval(() => {
      const channelInfo = this.channels.get(channel);
      if (!channelInfo || channelInfo.status !== ConnectionStatus.CONNECTED) {
        return;
      }

      // Simulate occasional feedback
      if (Math.random() > 0.9) {
        this.deliverMessage(channel, {
          type: "gesture_feedback",
          feedback: this.generateMockFeedback(),
          confidence: Math.random(),
          suggestions: this.generateMockSuggestions(),
          timestamp: new Date().toISOString(),
        });
      }
    }, 1000);

    this.simulationIntervals.set(channel, interval);
  }

  private simulateNotifications(channel: string): void {
    const interval = setInterval(() => {
      const channelInfo = this.channels.get(channel);
      if (!channelInfo || channelInfo.status !== ConnectionStatus.CONNECTED) {
        return;
      }

      // Simulate occasional notifications
      if (Math.random() > 0.95) {
        const notifications = [
          "New achievement unlocked!",
          "Practice reminder: Keep up the great work!",
          "System update available",
          "New story content added",
        ];

        this.deliverMessage(channel, {
          type: "notification",
          message:
            notifications[Math.floor(Math.random() * notifications.length)],
          priority: Math.random() > 0.8 ? "high" : "normal",
          timestamp: new Date().toISOString(),
        });
      }
    }, 5000);

    this.simulationIntervals.set(channel, interval);
  }

  private simulateGenericMessages(channel: string): void {
    const interval = setInterval(() => {
      const channelInfo = this.channels.get(channel);
      if (!channelInfo || channelInfo.status !== ConnectionStatus.CONNECTED) {
        return;
      }

      // Simulate heartbeat
      if (Math.random() > 0.7) {
        this.deliverMessage(channel, {
          type: "heartbeat",
          timestamp: new Date().toISOString(),
        });
      }
    }, 10000);

    this.simulationIntervals.set(channel, interval);
  }

  private generateMockLandmarks(): any {
    const landmarkCount = 21; // Typical for hand landmarks
    const landmarks = [];

    for (let i = 0; i < landmarkCount; i++) {
      landmarks.push({
        x: Math.random(),
        y: Math.random(),
        z: Math.random() * 0.1,
        visibility: Math.random(),
      });
    }

    return landmarks;
  }

  private generateMockFeedback(): string {
    const feedbacks = [
      "Great job! Your hand position looks good.",
      "Try to keep your hand more steady.",
      "Good signing! Consider slowing down a bit.",
      "Excellent form! Keep practicing.",
      "Your facial expression adds great meaning.",
      "Try to make your movements more distinct.",
    ];

    return feedbacks[Math.floor(Math.random() * feedbacks.length)];
  }

  private generateMockSuggestions(): string[] {
    const suggestions = [
      "Practice the hand shape more slowly",
      "Focus on facial expressions",
      "Keep your signing space consistent",
      "Try practicing in front of a mirror",
      "Watch the reference video again",
    ];

    const count = Math.floor(Math.random() * 3) + 1;
    const shuffled = suggestions.sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
  }
}

export default MockRealtimeService;
