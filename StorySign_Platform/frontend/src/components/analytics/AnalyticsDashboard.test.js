/**
 * Analytics Dashboard Test Suite
 * Tests for the enhanced analytics dashboard and reporting functionality
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import AnalyticsDashboard from "./AnalyticsDashboard";

// Mock Chart.js
jest.mock("chart.js", () => ({
  Chart: {
    register: jest.fn(),
  },
  CategoryScale: jest.fn(),
  LinearScale: jest.fn(),
  BarElement: jest.fn(),
  LineElement: jest.fn(),
  PointElement: jest.fn(),
  Title: jest.fn(),
  Tooltip: jest.fn(),
  Legend: jest.fn(),
  ArcElement: jest.fn(),
}));

// Mock react-chartjs-2
jest.mock("react-chartjs-2", () => ({
  Bar: ({ data, options }) => <div data-testid="bar-chart">Bar Chart</div>,
  Line: ({ data, options }) => <div data-testid="line-chart">Line Chart</div>,
  Pie: ({ data, options }) => <div data-testid="pie-chart">Pie Chart</div>,
  Doughnut: ({ data, options }) => (
    <div data-testid="doughnut-chart">Doughnut Chart</div>
  ),
}));

// Mock fetch
global.fetch = jest.fn();

const mockAnalyticsData = {
  platform_metrics: {
    total_users: 150,
    active_sessions: 45,
    practice_sessions: 320,
    stories_completed: 180,
    daily_activity: [
      { date: "2024-01-01", active_users: 25 },
      { date: "2024-01-02", active_users: 30 },
    ],
    module_usage: {
      asl_world: 65,
      harmony: 20,
      reconnect: 15,
    },
    learning_metrics: {
      average_score: 78.5,
      completion_rate: 85.2,
      avg_session_time: 24.5,
      gesture_accuracy: 82.3,
      score_trend: 2.1,
      completion_trend: 1.8,
      session_time_trend: -0.5,
      accuracy_trend: 3.2,
      progress_over_time: [
        { date: "2024-01-01", average_score: 75, completion_rate: 80 },
        { date: "2024-01-02", average_score: 76, completion_rate: 82 },
      ],
      difficulty_distribution: {
        easy: 120,
        medium: 150,
        hard: 50,
      },
      gesture_accuracy_by_type: [
        { gesture_type: "Hand Shapes", accuracy: 85.2 },
        { gesture_type: "Movement", accuracy: 78.9 },
      ],
      session_duration_trends: [
        { date: "2024-01-01", avg_duration: 22.5 },
        { date: "2024-01-02", avg_duration: 24.1 },
      ],
      top_performing_areas: [
        { name: "Finger Spelling", score: 88.3 },
        { name: "Basic Greetings", score: 86.7 },
      ],
      improvement_areas: [
        { name: "Complex Sentences", score: 65.2 },
        { name: "Spatial Grammar", score: 68.1 },
      ],
      recommendations: [
        { text: "Focus on spatial grammar exercises", priority: "high" },
        { text: "Practice complex sentence structures", priority: "high" },
      ],
    },
    performance_metrics: {
      avg_response_time: 145,
      avg_video_processing: 85,
      error_rate: 2.1,
      response_time_trends: [
        { timestamp: "2024-01-01T00:00:00Z", response_time: 150 },
      ],
      system_load: [
        { timestamp: "2024-01-01T00:00:00Z", cpu_usage: 45, memory_usage: 60 },
      ],
    },
    research_metrics: {
      total_participants: 125,
      consented_users: 98,
      data_points: 45620,
      research_sessions: 1250,
      learning_outcomes: [{ outcome: "Basic Communication", count: 85 }],
      engagement_heatmap: {
        hours: ["6AM", "9AM", "12PM"],
        monday: [12, 25, 35],
        tuesday: [15, 28, 38],
      },
      retention_data: [{ week: 1, retention_rate: 95.2 }],
      key_findings: [
        {
          text: "Users show 23% improvement in gesture accuracy after 4 weeks",
          confidence: 95,
        },
      ],
      statistical_tests: [
        { name: "Learning Improvement", p_value: 0.001, significant: true },
      ],
      educator_recommendations: [
        {
          text: "Schedule practice sessions in the evening for better retention",
          evidence_level: "Strong",
        },
      ],
    },
    total_events: 15420,
  },
};

describe("AnalyticsDashboard", () => {
  beforeEach(() => {
    fetch.mockClear();
    // Mock localStorage
    Object.defineProperty(window, "localStorage", {
      value: {
        getItem: jest.fn(() => "mock-token"),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      },
      writable: true,
    });
  });

  test("renders analytics dashboard with loading state", () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalyticsData,
    });

    render(<AnalyticsDashboard userRole="educator" />);

    expect(screen.getByText("Loading analytics...")).toBeInTheDocument();
  });

  test("renders analytics dashboard with data", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalyticsData,
    });

    render(<AnalyticsDashboard userRole="educator" />);

    await waitFor(() => {
      expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    });

    // Check if view selector buttons are present
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("Learning Analytics")).toBeInTheDocument();
    expect(screen.getByText("Performance")).toBeInTheDocument();
    expect(screen.getByText("Research")).toBeInTheDocument();
    expect(screen.getByText("Advanced Reports")).toBeInTheDocument();
    expect(screen.getByText("Export Data")).toBeInTheDocument();
  });

  test("switches between different dashboard views", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalyticsData,
    });

    render(<AnalyticsDashboard userRole="educator" />);

    await waitFor(() => {
      expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    });

    // Test switching to Learning Analytics view
    fireEvent.click(screen.getByText("Learning Analytics"));
    expect(screen.getByText("Average Score")).toBeInTheDocument();
    expect(screen.getByText("78.5%")).toBeInTheDocument();

    // Test switching to Performance view
    fireEvent.click(screen.getByText("Performance"));
    expect(screen.getByText("Avg Response Time")).toBeInTheDocument();
    expect(screen.getByText("145ms")).toBeInTheDocument();

    // Test switching to Research view
    fireEvent.click(screen.getByText("Research"));
    expect(screen.getByText("Total Participants")).toBeInTheDocument();
    expect(screen.getByText("125")).toBeInTheDocument();
  });

  test("displays learning insights and recommendations", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalyticsData,
    });

    render(<AnalyticsDashboard userRole="educator" />);

    await waitFor(() => {
      expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    });

    // Switch to Learning Analytics view
    fireEvent.click(screen.getByText("Learning Analytics"));

    // Check for insights panel
    expect(screen.getByText("Learning Insights")).toBeInTheDocument();
    expect(screen.getByText("Top Performing Areas")).toBeInTheDocument();
    expect(screen.getByText("Areas for Improvement")).toBeInTheDocument();
    expect(screen.getByText("Learning Recommendations")).toBeInTheDocument();

    // Check specific insights
    expect(screen.getByText("Finger Spelling")).toBeInTheDocument();
    expect(screen.getByText("Complex Sentences")).toBeInTheDocument();
    expect(
      screen.getByText("Focus on spatial grammar exercises")
    ).toBeInTheDocument();
  });

  test("displays research dashboard with privacy notice", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalyticsData,
    });

    render(<AnalyticsDashboard userRole="researcher" />);

    await waitFor(() => {
      expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    });

    // Switch to Research view
    fireEvent.click(screen.getByText("Research"));

    // Check research metrics
    expect(screen.getByText("Total Participants")).toBeInTheDocument();
    expect(screen.getByText("Consented Users")).toBeInTheDocument();
    expect(screen.getByText("Data Points Collected")).toBeInTheDocument();

    // Check privacy notice
    expect(screen.getByText("Privacy & Ethics Notice")).toBeInTheDocument();
    expect(
      screen.getByText(/All research data is anonymized/)
    ).toBeInTheDocument();

    // Check research insights
    expect(screen.getByText("Key Findings")).toBeInTheDocument();
    expect(screen.getByText("Statistical Significance")).toBeInTheDocument();
    expect(
      screen.getByText("Recommendations for Educators")
    ).toBeInTheDocument();
  });

  test("handles date range changes", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalyticsData,
    });

    render(<AnalyticsDashboard userRole="educator" />);

    await waitFor(() => {
      expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    });

    // Find date inputs by type
    const dateInputs = screen.getAllByDisplayValue(/2025-/);
    expect(dateInputs).toHaveLength(2);

    // Change start date
    fireEvent.change(dateInputs[0], { target: { value: "2025-01-15" } });

    // Verify the component handles the change
    expect(dateInputs[0].value).toBe("2025-01-15");
  });

  test("displays error state when API fails", async () => {
    fetch.mockRejectedValueOnce(new Error("API Error"));

    render(<AnalyticsDashboard userRole="educator" />);

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });

  test("shows charts in overview dashboard", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalyticsData,
    });

    render(<AnalyticsDashboard userRole="educator" />);

    await waitFor(() => {
      expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    });

    // Check for metric cards
    expect(screen.getByText("Total Users")).toBeInTheDocument();
    expect(screen.getByText("150")).toBeInTheDocument();
    expect(screen.getByText("Active Sessions")).toBeInTheDocument();
    expect(screen.getByText("45")).toBeInTheDocument();

    // Check for charts
    expect(screen.getByText("Daily Active Users")).toBeInTheDocument();
    expect(screen.getByText("Module Usage")).toBeInTheDocument();
  });

  test("displays performance metrics with trends", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalyticsData,
    });

    render(<AnalyticsDashboard userRole="educator" />);

    await waitFor(() => {
      expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    });

    // Switch to Performance view
    fireEvent.click(screen.getByText("Performance"));

    // Check performance metrics
    expect(screen.getByText("Avg Response Time")).toBeInTheDocument();
    expect(screen.getByText("145ms")).toBeInTheDocument();
    expect(screen.getByText("Video Processing")).toBeInTheDocument();
    expect(screen.getByText("85ms")).toBeInTheDocument();
    expect(screen.getByText("Error Rate")).toBeInTheDocument();
    expect(screen.getByText("2.10%")).toBeInTheDocument();

    // Check for performance charts
    expect(screen.getByText("Response Time Trends")).toBeInTheDocument();
    expect(screen.getByText("System Load")).toBeInTheDocument();
  });

  test("renders learning analytics with enhanced metrics", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalyticsData,
    });

    render(<AnalyticsDashboard userRole="educator" />);

    await waitFor(() => {
      expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    });

    // Switch to Learning Analytics view
    fireEvent.click(screen.getByText("Learning Analytics"));

    // Check enhanced metrics with trends
    expect(screen.getByText("Average Score")).toBeInTheDocument();
    expect(screen.getByText("78.5%")).toBeInTheDocument();
    // Check for trend indicators (they exist in the DOM as shown in the test output)
    const trendElements = screen.getAllByText(/↗|↘/);
    expect(trendElements.length).toBeGreaterThan(0);

    expect(screen.getByText("Completion Rate")).toBeInTheDocument();
    expect(screen.getByText("85.2%")).toBeInTheDocument();

    expect(screen.getByText("Gesture Accuracy")).toBeInTheDocument();
    expect(screen.getByText("82.3%")).toBeInTheDocument();

    // Check for additional charts
    expect(screen.getByText("Gesture Accuracy by Type")).toBeInTheDocument();
    expect(screen.getByText("Session Duration Trends")).toBeInTheDocument();
  });
});

describe("AnalyticsDashboard Integration", () => {
  test("integrates with export functionality", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalyticsData,
    });

    render(<AnalyticsDashboard userRole="educator" />);

    await waitFor(() => {
      expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    });

    // Switch to Export view
    fireEvent.click(screen.getByText("Export Data"));

    // Check export panel is rendered
    expect(screen.getByText("Export Configuration")).toBeInTheDocument();
    expect(screen.getByText("Export Format")).toBeInTheDocument();
    expect(screen.getByText("Privacy Settings")).toBeInTheDocument();
  });

  test("handles user role permissions correctly", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalyticsData,
    });

    // Test with researcher role
    const { rerender } = render(<AnalyticsDashboard userRole="researcher" />);

    await waitFor(() => {
      expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    });

    // Research view should be available for researchers
    expect(screen.getByText("Research")).toBeInTheDocument();

    // Test with educator role
    rerender(<AnalyticsDashboard userRole="educator" />);

    // All views should be available for educators
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("Learning Analytics")).toBeInTheDocument();
    expect(screen.getByText("Performance")).toBeInTheDocument();
    expect(screen.getByText("Research")).toBeInTheDocument();
  });
});
