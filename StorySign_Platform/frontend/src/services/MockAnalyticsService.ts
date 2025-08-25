/**
 * Mock Analytics Service
 *
 * Provides a mock implementation of the AnalyticsService interface
 * for development and testing purposes.
 */

import {
  AnalyticsService,
  AnalyticsEvent,
  AnalyticsQuery,
} from "../types/module";

export class MockAnalyticsService implements AnalyticsService {
  private events: AnalyticsEvent[] = [];
  private userActions: Array<{
    action: string;
    data?: any;
    timestamp: string;
  }> = [];
  private performanceMetrics: Array<{
    metric: string;
    value: number;
    metadata?: any;
    timestamp: string;
  }> = [];

  constructor() {
    console.log("MockAnalyticsService: Initialized");
  }

  trackEvent(event: AnalyticsEvent): void {
    const enrichedEvent = {
      ...event,
      timestamp: event.timestamp || new Date().toISOString(),
    };

    this.events.push(enrichedEvent);

    console.log("MockAnalytics: Event tracked:", enrichedEvent);

    // Simulate real-time analytics processing
    this.processEventInBackground(enrichedEvent);
  }

  trackUserAction(action: string, data?: Record<string, any>): void {
    const actionRecord = {
      action,
      data,
      timestamp: new Date().toISOString(),
    };

    this.userActions.push(actionRecord);

    console.log("MockAnalytics: User action tracked:", actionRecord);

    // Also track as an event
    this.trackEvent({
      type: "user_action",
      moduleName: "platform",
      eventData: { action, ...data },
      timestamp: actionRecord.timestamp,
    });
  }

  trackPerformance(
    metric: string,
    value: number,
    metadata?: Record<string, any>
  ): void {
    const performanceRecord = {
      metric,
      value,
      metadata,
      timestamp: new Date().toISOString(),
    };

    this.performanceMetrics.push(performanceRecord);

    console.log(
      "MockAnalytics: Performance metric tracked:",
      performanceRecord
    );

    // Also track as an event
    this.trackEvent({
      type: "performance_metric",
      moduleName: "platform",
      eventData: { metric, value, ...metadata },
      timestamp: performanceRecord.timestamp,
    });
  }

  async getAnalytics(query: AnalyticsQuery): Promise<any> {
    console.log("MockAnalytics: Analytics query:", query);

    let filteredEvents = [...this.events];

    // Apply filters
    if (query.userId) {
      filteredEvents = filteredEvents.filter(
        (event) => event.userId === query.userId
      );
    }

    if (query.moduleId) {
      filteredEvents = filteredEvents.filter(
        (event) => event.moduleName === query.moduleId
      );
    }

    if (query.eventType) {
      filteredEvents = filteredEvents.filter(
        (event) => event.type === query.eventType
      );
    }

    if (query.dateRange) {
      const startDate = new Date(query.dateRange.start);
      const endDate = new Date(query.dateRange.end);

      filteredEvents = filteredEvents.filter((event) => {
        const eventDate = new Date(event.timestamp);
        return eventDate >= startDate && eventDate <= endDate;
      });
    }

    // Apply aggregation
    let result: any;

    switch (query.aggregation) {
      case "count":
        result = {
          aggregation: "count",
          value: filteredEvents.length,
          events: filteredEvents,
        };
        break;

      case "sum":
        result = {
          aggregation: "sum",
          value: filteredEvents.reduce((sum, event) => {
            const value = event.eventData?.value || 0;
            return sum + (typeof value === "number" ? value : 0);
          }, 0),
          events: filteredEvents,
        };
        break;

      case "avg":
        const values = filteredEvents
          .map((event) => event.eventData?.value)
          .filter((value) => typeof value === "number");

        result = {
          aggregation: "avg",
          value:
            values.length > 0
              ? values.reduce((sum, val) => sum + val, 0) / values.length
              : 0,
          events: filteredEvents,
        };
        break;

      case "min":
        const minValues = filteredEvents
          .map((event) => event.eventData?.value)
          .filter((value) => typeof value === "number");

        result = {
          aggregation: "min",
          value: minValues.length > 0 ? Math.min(...minValues) : 0,
          events: filteredEvents,
        };
        break;

      case "max":
        const maxValues = filteredEvents
          .map((event) => event.eventData?.value)
          .filter((value) => typeof value === "number");

        result = {
          aggregation: "max",
          value: maxValues.length > 0 ? Math.max(...maxValues) : 0,
          events: filteredEvents,
        };
        break;

      default:
        result = {
          aggregation: "none",
          events: filteredEvents,
          summary: this.generateSummary(filteredEvents),
        };
    }

    console.log("MockAnalytics: Query result:", result);
    return result;
  }

  // Additional methods for testing and development
  public getAllEvents(): AnalyticsEvent[] {
    return [...this.events];
  }

  public getAllUserActions(): Array<{
    action: string;
    data?: any;
    timestamp: string;
  }> {
    return [...this.userActions];
  }

  public getAllPerformanceMetrics(): Array<{
    metric: string;
    value: number;
    metadata?: any;
    timestamp: string;
  }> {
    return [...this.performanceMetrics];
  }

  public clearAllData(): void {
    this.events = [];
    this.userActions = [];
    this.performanceMetrics = [];
    console.log("MockAnalytics: All data cleared");
  }

  public getEventsByModule(moduleName: string): AnalyticsEvent[] {
    return this.events.filter((event) => event.moduleName === moduleName);
  }

  public getEventsByType(eventType: string): AnalyticsEvent[] {
    return this.events.filter((event) => event.type === eventType);
  }

  public getEventsByUser(userId: string): AnalyticsEvent[] {
    return this.events.filter((event) => event.userId === userId);
  }

  public generateReport(timeRange?: { start: string; end: string }): any {
    let events = this.events;

    if (timeRange) {
      const startDate = new Date(timeRange.start);
      const endDate = new Date(timeRange.end);

      events = events.filter((event) => {
        const eventDate = new Date(event.timestamp);
        return eventDate >= startDate && eventDate <= endDate;
      });
    }

    const report = {
      totalEvents: events.length,
      timeRange: timeRange || { start: "all time", end: "all time" },
      eventsByType: this.groupBy(events, "type"),
      eventsByModule: this.groupBy(events, "moduleName"),
      eventsByUser: this.groupBy(
        events.filter((e) => e.userId),
        "userId"
      ),
      topEvents: this.getTopEvents(events, 10),
      performanceSummary: this.getPerformanceSummary(),
      generatedAt: new Date().toISOString(),
    };

    console.log("MockAnalytics: Generated report:", report);
    return report;
  }

  private processEventInBackground(event: AnalyticsEvent): void {
    // Simulate background processing
    setTimeout(() => {
      // Could trigger alerts, update dashboards, etc.
      if (
        event.type === "error" ||
        event.type === "module_initialization_failed"
      ) {
        console.warn("MockAnalytics: Alert - Error event detected:", event);
      }
    }, 100);
  }

  private generateSummary(events: AnalyticsEvent[]): any {
    return {
      totalEvents: events.length,
      eventTypes: [...new Set(events.map((e) => e.type))],
      modules: [...new Set(events.map((e) => e.moduleName))],
      users: [...new Set(events.filter((e) => e.userId).map((e) => e.userId))],
      timeRange: {
        earliest:
          events.length > 0
            ? Math.min(...events.map((e) => new Date(e.timestamp).getTime()))
            : null,
        latest:
          events.length > 0
            ? Math.max(...events.map((e) => new Date(e.timestamp).getTime()))
            : null,
      },
    };
  }

  private groupBy(array: any[], key: string): Record<string, number> {
    return array.reduce((groups, item) => {
      const value = item[key];
      groups[value] = (groups[value] || 0) + 1;
      return groups;
    }, {});
  }

  private getTopEvents(
    events: AnalyticsEvent[],
    limit: number
  ): Array<{ type: string; count: number }> {
    const eventCounts = this.groupBy(events, "type");

    return Object.entries(eventCounts)
      .map(([type, count]) => ({ type, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, limit);
  }

  private getPerformanceSummary(): any {
    if (this.performanceMetrics.length === 0) {
      return { message: "No performance metrics available" };
    }

    const metricsByName = this.groupBy(this.performanceMetrics, "metric");
    const summary: Record<string, any> = {};

    Object.keys(metricsByName).forEach((metricName) => {
      const metrics = this.performanceMetrics.filter(
        (m) => m.metric === metricName
      );
      const values = metrics.map((m) => m.value);

      summary[metricName] = {
        count: values.length,
        min: Math.min(...values),
        max: Math.max(...values),
        avg: values.reduce((sum, val) => sum + val, 0) / values.length,
        latest: metrics[metrics.length - 1]?.value,
      };
    });

    return summary;
  }
}

export default MockAnalyticsService;
