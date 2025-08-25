/**
 * ASL World Module Interface Implementation
 *
 * Implements the ModuleInterface contract for the ASL World learning module.
 * This provides standardized integration with the platform infrastructure.
 */

import React, { ReactNode } from "react";
import { BaseModule } from "../../core/BaseModule";
import {
  ModuleMetadata,
  ModuleContext,
  Permission,
  ModuleConfig,
} from "../../types/module";
import ASLWorldModule from "./ASLWorldModule";

// ASL World specific data types
export interface ASLWorldUserData {
  practiceHistory: PracticeSession[];
  preferences: ASLWorldPreferences;
  progress: LearningProgress;
  achievements: Achievement[];
}

export interface PracticeSession {
  id: string;
  storyId: string;
  storyTitle: string;
  difficulty: string;
  startTime: string;
  endTime?: string;
  sentences: SentenceAttempt[];
  overallScore?: number;
  completed: boolean;
}

export interface SentenceAttempt {
  sentenceIndex: number;
  targetSentence: string;
  attempts: number;
  bestScore: number;
  feedback: string[];
  landmarkData?: any;
  timestamp: string;
}

export interface ASLWorldPreferences {
  preferredDifficulty: string;
  autoAdvance: boolean;
  feedbackVerbosity: "minimal" | "normal" | "detailed";
  practiceReminders: boolean;
  videoQuality: "low" | "medium" | "high" | "auto";
}

export interface LearningProgress {
  totalPracticeTime: number;
  storiesCompleted: number;
  sentencesCompleted: number;
  averageScore: number;
  skillLevels: Record<string, number>;
  streakDays: number;
  lastPracticeDate: string;
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  unlockedAt: string;
  category: "practice" | "progress" | "social" | "special";
}

// ASL World Module Props Interface
export interface ASLWorldModuleProps {
  // Story management
  storyData?: any;
  selectedStory?: any;
  onStorySelect?: (story: any) => void;
  onStoryGenerate?: (params: any) => void;
  isGeneratingStory?: boolean;

  // Practice session management
  currentSentenceIndex?: number;
  latestFeedback?: any;
  onPracticeControl?: (action: string, index?: number) => void;
  isProcessingFeedback?: boolean;
  practiceStarted?: boolean;
  onStartPractice?: () => void;
  gestureState?: string;

  // Connection and streaming
  connectionStatus?: string;
  streamingConnectionStatus?: string;
  onFrameCapture?: (frame: any) => void;
  processedFrameData?: any;
  streamingStats?: any;
  optimizationSettings?: any;
  onOptimizationChange?: (settings: any) => void;

  // Additional props
  children?: ReactNode;
}

export class ASLWorldModuleInterface extends BaseModule {
  readonly metadata: ModuleMetadata = {
    id: "asl-world",
    name: "ASL World",
    version: "1.0.0",
    description:
      "Interactive American Sign Language learning environment with real-time gesture recognition",
    author: "StorySign Team",
    dependencies: ["video-processing", "ai-services"],
    permissions: [
      Permission.READ_OWN_DATA,
      Permission.WRITE_OWN_DATA,
      Permission.CREATE_CONTENT,
      Permission.VIEW_ANALYTICS,
    ],
    icon: "🌍",
    route: "/asl-world",
  };

  private moduleProps: ASLWorldModuleProps = {};
  private practiceSessionId: string | null = null;
  private currentUserData: ASLWorldUserData | null = null;

  constructor(config?: Partial<ModuleConfig>) {
    super({
      enabled: true,
      settings: {
        defaultDifficulty: "mid_level",
        autoSaveProgress: true,
        enableAnalytics: true,
        maxSessionDuration: 3600000, // 1 hour in ms
        ...config?.settings,
      },
      permissions: [
        Permission.READ_OWN_DATA,
        Permission.WRITE_OWN_DATA,
        Permission.CREATE_CONTENT,
        Permission.VIEW_ANALYTICS,
      ],
      dependencies: ["video-processing", "ai-services"],
      ...config,
    });
  }

  // Lifecycle implementation
  protected async onInitialize(context: ModuleContext): Promise<void> {
    console.log("Initializing ASL World module...");

    // Initialize user data if user is logged in
    if (context.user) {
      await this.loadUserData(context.user.id);
    }

    // Set up real-time connections for video processing
    await this.setupRealtimeConnections(context);

    // Register plugin hooks for extensibility
    this.registerDefaultPluginHooks();

    console.log("ASL World module initialized successfully");
  }

  protected async onCleanup(): Promise<void> {
    console.log("Cleaning up ASL World module...");

    // Save any pending user data
    if (this.context?.user && this.currentUserData) {
      await this.saveUserData(this.context.user.id, this.currentUserData);
    }

    // Clean up real-time connections
    if (this.context) {
      await this.context.realtime.disconnect("video-processing");
      await this.context.realtime.disconnect("asl-feedback");
    }

    // End any active practice session
    if (this.practiceSessionId) {
      await this.endPracticeSession();
    }

    console.log("ASL World module cleanup completed");
  }

  protected async onHealthCheck(): Promise<string[]> {
    const issues: string[] = [];

    // Check video processing connection
    if (this.context) {
      const videoStatus =
        this.context.realtime.getConnectionStatus("video-processing");
      if (videoStatus !== "connected") {
        issues.push(`Video processing connection status: ${videoStatus}`);
      }

      // Check AI services availability
      try {
        // This would typically ping the AI services
        console.log("Checking AI services availability...");
      } catch (error) {
        issues.push(`AI services unavailable: ${error.message}`);
      }
    }

    return issues;
  }

  // Data access implementation
  async getUserData(userId: string): Promise<ASLWorldUserData> {
    const data = await super.getUserData(userId);

    // Return default data structure if no data exists
    if (!data) {
      const defaultData: ASLWorldUserData = {
        practiceHistory: [],
        preferences: {
          preferredDifficulty:
            this.config.settings.defaultDifficulty || "mid_level",
          autoAdvance: false,
          feedbackVerbosity: "normal",
          practiceReminders: true,
          videoQuality: "auto",
        },
        progress: {
          totalPracticeTime: 0,
          storiesCompleted: 0,
          sentencesCompleted: 0,
          averageScore: 0,
          skillLevels: {},
          streakDays: 0,
          lastPracticeDate: "",
        },
        achievements: [],
      };

      await this.saveUserData(userId, defaultData);
      return defaultData;
    }

    return data as ASLWorldUserData;
  }

  async saveUserData(userId: string, data: ASLWorldUserData): Promise<void> {
    await super.saveUserData(userId, data);
    this.currentUserData = data;

    // Track data save event
    this.trackEvent({
      type: "user_data_updated",
      moduleName: this.metadata.id,
      eventData: {
        practiceHistoryCount: data.practiceHistory.length,
        totalPracticeTime: data.progress.totalPracticeTime,
        storiesCompleted: data.progress.storiesCompleted,
      },
      userId,
      timestamp: new Date().toISOString(),
    });
  }

  // Component rendering
  renderComponent(props: ASLWorldModuleProps): ReactNode {
    // Merge props with module-specific enhancements
    const enhancedProps = {
      ...props,
      ...this.moduleProps,
      // Add module-specific event handlers
      onStoryGenerate: this.handleStoryGenerate.bind(this),
      onPracticeControl: this.handlePracticeControl.bind(this),
      onStartPractice: this.handleStartPractice.bind(this),
    };

    return React.createElement(ASLWorldModule, enhancedProps);
  }

  // Module-specific methods
  public updateProps(props: Partial<ASLWorldModuleProps>): void {
    this.moduleProps = { ...this.moduleProps, ...props };
  }

  public async startPracticeSession(storyData: any): Promise<string> {
    if (!this.context?.user) {
      throw new Error("User must be logged in to start practice session");
    }

    const sessionId = `session_${Date.now()}_${Math.random()
      .toString(36)
      .substr(2, 9)}`;

    const sessionData = {
      id: sessionId,
      userId: this.context.user.id,
      storyId: storyData.id || "generated",
      storyTitle: storyData.title,
      difficulty: storyData.difficulty || "unknown",
      startTime: new Date().toISOString(),
      sentences: [],
      completed: false,
    };

    // Save session to database
    await this.context.database.createSession(sessionData);
    this.practiceSessionId = sessionId;

    // Track session start
    this.trackEvent({
      type: "practice_session_started",
      moduleName: this.metadata.id,
      eventData: {
        sessionId,
        storyTitle: storyData.title,
        difficulty: storyData.difficulty,
        sentenceCount: storyData.sentences?.length || 0,
      },
      userId: this.context.user.id,
      sessionId,
      timestamp: new Date().toISOString(),
    });

    return sessionId;
  }

  public async endPracticeSession(): Promise<void> {
    if (!this.practiceSessionId || !this.context?.user) {
      return;
    }

    const sessionData = await this.context.database.getSession(
      this.practiceSessionId
    );
    if (sessionData) {
      sessionData.endTime = new Date().toISOString();
      await this.context.database.updateSession(
        this.practiceSessionId,
        sessionData
      );

      // Update user progress
      await this.updateUserProgress(sessionData);

      // Track session end
      this.trackEvent({
        type: "practice_session_ended",
        moduleName: this.metadata.id,
        eventData: {
          sessionId: this.practiceSessionId,
          duration:
            new Date().getTime() - new Date(sessionData.startTime).getTime(),
          completed: sessionData.completed,
          sentencesCompleted: sessionData.sentences?.length || 0,
        },
        userId: this.context.user.id,
        sessionId: this.practiceSessionId,
        timestamp: new Date().toISOString(),
      });
    }

    this.practiceSessionId = null;
  }

  // Private helper methods
  private async loadUserData(userId: string): Promise<void> {
    try {
      this.currentUserData = await this.getUserData(userId);
    } catch (error) {
      console.error("Failed to load user data:", error);
      // Initialize with default data
      this.currentUserData = await this.getUserData(userId);
    }
  }

  private async setupRealtimeConnections(
    context: ModuleContext
  ): Promise<void> {
    // Set up video processing channel
    await context.realtime.connect("video-processing");
    context.realtime.subscribe(
      "video-processing",
      this.handleVideoProcessingMessage.bind(this)
    );

    // Set up feedback channel
    await context.realtime.connect("asl-feedback");
    context.realtime.subscribe(
      "asl-feedback",
      this.handleFeedbackMessage.bind(this)
    );
  }

  private registerDefaultPluginHooks(): void {
    const hooks = [
      {
        type: "before" as const,
        target: "asl-world.practice-session.start",
        handler: async (context: any) => {
          console.log("Before practice session start hook:", context);
          return context;
        },
      },
      {
        type: "after" as const,
        target: "asl-world.sentence.completed",
        handler: async (context: any) => {
          console.log("After sentence completed hook:", context);
          return context;
        },
      },
    ];

    this.registerPluginHooks(hooks);
  }

  private handleVideoProcessingMessage(message: any): void {
    // Handle real-time video processing messages
    if (this.moduleProps.onFrameCapture) {
      this.moduleProps.onFrameCapture(message);
    }
  }

  private handleFeedbackMessage(message: any): void {
    // Handle AI feedback messages
    console.log("Received feedback message:", message);
  }

  private async handleStoryGenerate(params: any): Promise<void> {
    if (!this.context?.user) {
      console.warn("Cannot generate story - user not logged in");
      return;
    }

    this.trackEvent({
      type: "story_generation_requested",
      moduleName: this.metadata.id,
      eventData: params,
      userId: this.context.user.id,
      timestamp: new Date().toISOString(),
    });

    // Delegate to original handler if provided
    if (this.moduleProps.onStoryGenerate) {
      await this.moduleProps.onStoryGenerate(params);
    }
  }

  private async handlePracticeControl(
    action: string,
    index?: number
  ): Promise<void> {
    if (!this.context?.user) {
      console.warn("Cannot handle practice control - user not logged in");
      return;
    }

    this.trackEvent({
      type: "practice_control_action",
      moduleName: this.metadata.id,
      eventData: { action, sentenceIndex: index },
      userId: this.context.user.id,
      sessionId: this.practiceSessionId || undefined,
      timestamp: new Date().toISOString(),
    });

    // Handle session lifecycle
    if (action === "complete_story" || action === "new_story") {
      await this.endPracticeSession();
    }

    // Delegate to original handler if provided
    if (this.moduleProps.onPracticeControl) {
      await this.moduleProps.onPracticeControl(action, index);
    }
  }

  private async handleStartPractice(): Promise<void> {
    if (!this.context?.user) {
      console.warn("Cannot start practice - user not logged in");
      return;
    }

    // Start a new practice session if one doesn't exist
    if (!this.practiceSessionId && this.moduleProps.selectedStory) {
      await this.startPracticeSession(this.moduleProps.selectedStory);
    }

    // Delegate to original handler if provided
    if (this.moduleProps.onStartPractice) {
      this.moduleProps.onStartPractice();
    }
  }

  private async updateUserProgress(sessionData: any): Promise<void> {
    if (!this.context?.user || !this.currentUserData) {
      return;
    }

    const userData = this.currentUserData;

    // Update practice history
    userData.practiceHistory.push(sessionData);

    // Update progress metrics
    const sessionDuration =
      new Date(sessionData.endTime).getTime() -
      new Date(sessionData.startTime).getTime();
    userData.progress.totalPracticeTime += sessionDuration;

    if (sessionData.completed) {
      userData.progress.storiesCompleted++;
    }

    userData.progress.sentencesCompleted += sessionData.sentences?.length || 0;
    userData.progress.lastPracticeDate = new Date().toISOString();

    // Calculate average score
    const completedSessions = userData.practiceHistory.filter(
      (s) => s.completed && s.overallScore
    );
    if (completedSessions.length > 0) {
      userData.progress.averageScore =
        completedSessions.reduce((sum, s) => sum + s.overallScore, 0) /
        completedSessions.length;
    }

    // Save updated data
    await this.saveUserData(this.context.user.id, userData);
  }
}

export default ASLWorldModuleInterface;
