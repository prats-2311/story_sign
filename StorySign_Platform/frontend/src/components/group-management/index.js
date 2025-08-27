/**
 * Group Management Components
 *
 * This module provides comprehensive group management features for educators
 * including assignments, analytics, notifications, and communication tools.
 */

export { default as AssignmentManager } from "./AssignmentManager";
export { default as GroupAnalyticsDashboard } from "./GroupAnalyticsDashboard";
export { default as NotificationCenter } from "./NotificationCenter";

// Re-export for convenience
export const GroupManagementComponents = {
  AssignmentManager: require("./AssignmentManager").default,
  GroupAnalyticsDashboard: require("./GroupAnalyticsDashboard").default,
  NotificationCenter: require("./NotificationCenter").default,
};

/**
 * Usage Examples:
 *
 * // Assignment Management
 * import { AssignmentManager } from './components/group-management';
 * <AssignmentManager
 *   groupId="group_123"
 *   userRole="educator"
 *   onAssignmentCreated={handleAssignmentCreated}
 * />
 *
 * // Analytics Dashboard
 * import { GroupAnalyticsDashboard } from './components/group-management';
 * <GroupAnalyticsDashboard
 *   groupId="group_123"
 *   userRole="educator"
 * />
 *
 * // Notification Center
 * import { NotificationCenter } from './components/group-management';
 * <NotificationCenter
 *   userId="user_123"
 *   onNotificationClick={handleNotificationClick}
 * />
 */
