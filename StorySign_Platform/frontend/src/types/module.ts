/**
 * Module Interface Standard for StorySign Platform
 *
 * This file defines the standardized interfaces that all learning modules
 * must implement to integrate with the platform infrastructure.
 */

import { ReactNode, ComponentType } from "react";

// Core module metadata interface
export interface ModuleMetadata {
  readonly id: string;
  readonly name: string;
  readonly version: string;
  readonly description: string;
  readonly author: string;
  readonly dependencies: string[];
  readonly permissions: Permission[];
  readonly icon: string;
  readonly route: string;
}

// Permission system for module access control
export enum Permission {
  READ_OWN_DATA = "read:own_data",
  WRITE_OWN_DATA = "write:own_data",
  READ_PUBLIC_CONTENT = "read:public_content",
  CREATE_CONTENT = "create:content",
  MODERATE_CONTENT = "moderate:content",
  MANAGE_USERS = "manage:users",
  INSTALL_PLUGINS = "install:plugins",
  VIEW_ANALYTICS = "view:analytics",
  EXPORT_DATA = "export:data",
}

// User interface for module context
export interface User {
  id: string;
  email: string;
  username: string;
  firstName?: string;
  lastName?: string;
  role: UserRole;
  preferences: Record<string, any>;
  profile?: UserProfile;
}

export enum UserRole {
  LEARNER = "learner",
  EDUCATOR = "educator",
  CONTENT_CREATOR = "content_creator",
  RESEARCHER = "researcher",
  ADMIN = "admin",
}

export interface UserProfile {
  avatarUrl?: string;
  bio?: string;
  timezone?: string;
  language?: string;
  learningGoals?: Record<string, any>;
  accessibilitySettings?: Record<string, any>;
}

// Analytics event interface
export interface AnalyticsEvent {
  type: string;
  moduleName: string;
  eventData: Record<string, any>;
  userId?: string;
  sessionId?: string;
  timestamp: string;
}

// Database service interface for module data access
export interface DatabaseService {
  // User data operations
  getUserData(userId: string, dataType: string): Promise<any>;
  saveUserData(userId: string, dataType: string, data: any): Promise<void>;
  deleteUserData(userId: string, dataType: string): Promise<void>;

  // Content operations
  getContent(contentId: string): Promise<any>;
  saveContent(content: any): Promise<string>;
  searchContent(query: ContentQuery): Promise<any[]>;

  // Progress tracking
  getProgress(userId: string, moduleId: string): Promise<any>;
  updateProgress(
    userId: string,
    moduleId: string,
    progress: any
  ): Promise<void>;

  // Session management
  createSession(sessionData: any): Promise<string>;
  updateSession(sessionId: string, sessionData: any): Promise<void>;
  getSession(sessionId: string): Promise<any>;
}

export interface ContentQuery {
  type?: string;
  difficulty?: string;
  tags?: string[];
  limit?: number;
  offset?: number;
}

// Analytics service interface
export interface AnalyticsService {
  trackEvent(event: AnalyticsEvent): void;
  trackUserAction(action: string, data?: Record<string, any>): void;
  trackPerformance(
    metric: string,
    value: number,
    metadata?: Record<string, any>
  ): void;
  getAnalytics(query: AnalyticsQuery): Promise<any>;
}

export interface AnalyticsQuery {
  userId?: string;
  moduleId?: string;
  eventType?: string;
  dateRange?: {
    start: string;
    end: string;
  };
  aggregation?: "count" | "sum" | "avg" | "min" | "max";
}

// Plugin service interface
export interface PluginService {
  getAvailablePlugins(): Promise<PluginInfo[]>;
  loadPlugin(pluginId: string): Promise<Plugin>;
  unloadPlugin(pluginId: string): Promise<void>;
  executeHook(hookName: string, context: any): Promise<any>;
  registerHook(hookName: string, handler: HookHandler): void;
}

export interface PluginInfo {
  id: string;
  name: string;
  version: string;
  description: string;
  isLoaded: boolean;
  permissions: Permission[];
}

export interface Plugin {
  info: PluginInfo;
  hooks: PluginHook[];
  components: ComponentType[];
  services: any[];
}

export interface PluginHook {
  type: "before" | "after" | "replace";
  target: string;
  handler: HookHandler;
}

export type HookHandler = (context: HookContext) => Promise<any>;

export interface HookContext {
  moduleId: string;
  userId?: string;
  data: any;
  metadata: Record<string, any>;
}

// Real-time service interface for WebSocket communication
export interface RealtimeService {
  connect(channel: string): Promise<void>;
  disconnect(channel: string): Promise<void>;
  send(channel: string, message: any): void;
  subscribe(channel: string, handler: MessageHandler): void;
  unsubscribe(channel: string, handler: MessageHandler): void;
  getConnectionStatus(channel: string): ConnectionStatus;
}

export type MessageHandler = (message: any) => void;

export enum ConnectionStatus {
  CONNECTED = "connected",
  CONNECTING = "connecting",
  DISCONNECTED = "disconnected",
  ERROR = "error",
}

// Module context interface - provides access to platform services
export interface ModuleContext {
  user: User | null;
  database: DatabaseService;
  analytics: AnalyticsService;
  plugins: PluginService;
  realtime: RealtimeService;
  platform: PlatformService;
}

// Platform service interface for cross-module communication
export interface PlatformService {
  navigateToModule(moduleId: string, params?: Record<string, any>): void;
  showNotification(
    message: string,
    type: NotificationType,
    duration?: number
  ): void;
  getCurrentTheme(): string;
  changeTheme(theme: string): void;
  getAccessibilitySettings(): Record<string, any>;
  updateAccessibilitySettings(settings: Record<string, any>): void;
}

export enum NotificationType {
  INFO = "info",
  SUCCESS = "success",
  WARNING = "warning",
  ERROR = "error",
}

// Module lifecycle states
export enum ModuleState {
  UNINITIALIZED = "uninitialized",
  INITIALIZING = "initializing",
  READY = "ready",
  ERROR = "error",
  DESTROYED = "destroyed",
}

// Module configuration interface
export interface ModuleConfig {
  enabled: boolean;
  settings: Record<string, any>;
  permissions: Permission[];
  dependencies: string[];
}

// Main module interface that all modules must implement
export interface ModuleInterface {
  // Module metadata
  readonly metadata: ModuleMetadata;

  // Current module state
  readonly state: ModuleState;

  // Module configuration
  config: ModuleConfig;

  // Lifecycle methods
  initialize(context: ModuleContext): Promise<void>;
  cleanup(): Promise<void>;
  onConfigChange(newConfig: ModuleConfig): Promise<void>;

  // Data access methods
  getUserData(userId: string): Promise<any>;
  saveUserData(userId: string, data: any): Promise<void>;

  // Analytics integration
  trackEvent(event: AnalyticsEvent): void;

  // Plugin integration
  registerPluginHooks(hooks: PluginHook[]): void;

  // Component rendering
  renderComponent(props: any): ReactNode;

  // Health check
  healthCheck(): Promise<ModuleHealthStatus>;
}

export interface ModuleHealthStatus {
  healthy: boolean;
  issues: string[];
  lastChecked: string;
  performance: {
    responseTime: number;
    memoryUsage: number;
    errorRate: number;
  };
}

// Module registration interface
export interface ModuleRegistration {
  module: ModuleInterface;
  priority: number;
  autoStart: boolean;
  dependencies: string[];
}

// Module manager interface for platform-level module management
export interface ModuleManager {
  registerModule(registration: ModuleRegistration): Promise<void>;
  unregisterModule(moduleId: string): Promise<void>;
  getModule(moduleId: string): ModuleInterface | null;
  getAllModules(): ModuleInterface[];
  getModulesByState(state: ModuleState): ModuleInterface[];
  initializeModule(moduleId: string): Promise<void>;
  destroyModule(moduleId: string): Promise<void>;
  reloadModule(moduleId: string): Promise<void>;
}

// All interfaces and types are already exported above with their declarations
