/**
 * Analytics Charts Components
 * Reusable chart components for analytics dashboard
 */

import React from "react";
import { Bar, Line, Pie, Doughnut } from "react-chartjs-2";

// User Activity Chart
export const UserActivityChart = ({ data }) => {
  const chartData = {
    labels: data.map((item) => item.date) || [],
    datasets: [
      {
        label: "Active Users",
        data: data.map((item) => item.active_users) || [],
        backgroundColor: "rgba(54, 162, 235, 0.6)",
        borderColor: "rgba(54, 162, 235, 1)",
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
      title: {
        display: true,
        text: "Daily Active Users",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return <Bar data={chartData} options={options} />;
};

// Module Usage Chart
export const ModuleUsageChart = ({ data }) => {
  const chartData = {
    labels: Object.keys(data),
    datasets: [
      {
        data: Object.values(data),
        backgroundColor: [
          "rgba(255, 99, 132, 0.6)",
          "rgba(54, 162, 235, 0.6)",
          "rgba(255, 205, 86, 0.6)",
          "rgba(75, 192, 192, 0.6)",
          "rgba(153, 102, 255, 0.6)",
        ],
        borderColor: [
          "rgba(255, 99, 132, 1)",
          "rgba(54, 162, 235, 1)",
          "rgba(255, 205, 86, 1)",
          "rgba(75, 192, 192, 1)",
          "rgba(153, 102, 255, 1)",
        ],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "right",
      },
    },
  };

  return <Pie data={chartData} options={options} />;
};
// Learning Progress Chart
export const LearningProgressChart = ({ data }) => {
  const chartData = {
    labels: data.map((item) => item.date) || [],
    datasets: [
      {
        label: "Average Score",
        data: data.map((item) => item.average_score) || [],
        borderColor: "rgba(75, 192, 192, 1)",
        backgroundColor: "rgba(75, 192, 192, 0.2)",
        tension: 0.1,
      },
      {
        label: "Completion Rate",
        data: data.map((item) => item.completion_rate) || [],
        borderColor: "rgba(255, 99, 132, 1)",
        backgroundColor: "rgba(255, 99, 132, 0.2)",
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
  };

  return <Line data={chartData} options={options} />;
};

// Difficulty Distribution Chart
export const DifficultyDistributionChart = ({ data }) => {
  const chartData = {
    labels: Object.keys(data),
    datasets: [
      {
        label: "Sessions by Difficulty",
        data: Object.values(data),
        backgroundColor: [
          "rgba(76, 175, 80, 0.6)",
          "rgba(255, 193, 7, 0.6)",
          "rgba(244, 67, 54, 0.6)",
        ],
        borderColor: [
          "rgba(76, 175, 80, 1)",
          "rgba(255, 193, 7, 1)",
          "rgba(244, 67, 54, 1)",
        ],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return <Bar data={chartData} options={options} />;
};

// Response Time Chart
export const ResponseTimeChart = ({ data }) => {
  const chartData = {
    labels: data.map((item) => item.timestamp) || [],
    datasets: [
      {
        label: "Response Time (ms)",
        data: data.map((item) => item.response_time) || [],
        borderColor: "rgba(153, 102, 255, 1)",
        backgroundColor: "rgba(153, 102, 255, 0.2)",
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return <Line data={chartData} options={options} />;
};
// System Load Chart
export const SystemLoadChart = ({ data }) => {
  const chartData = {
    labels: data.map((item) => item.timestamp) || [],
    datasets: [
      {
        label: "CPU Usage (%)",
        data: data.map((item) => item.cpu_usage) || [],
        borderColor: "rgba(255, 99, 132, 1)",
        backgroundColor: "rgba(255, 99, 132, 0.2)",
        tension: 0.1,
      },
      {
        label: "Memory Usage (%)",
        data: data.map((item) => item.memory_usage) || [],
        borderColor: "rgba(54, 162, 235, 1)",
        backgroundColor: "rgba(54, 162, 235, 0.2)",
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
  };

  return <Line data={chartData} options={options} />;
};

// Gesture Accuracy Chart
export const GestureAccuracyChart = ({ data }) => {
  const chartData = {
    labels: data.map((item) => item.gesture_type) || [],
    datasets: [
      {
        label: "Accuracy (%)",
        data: data.map((item) => item.accuracy) || [],
        backgroundColor: "rgba(75, 192, 192, 0.6)",
        borderColor: "rgba(75, 192, 192, 1)",
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
  };

  return <Bar data={chartData} options={options} />;
};

// Session Duration Chart
export const SessionDurationChart = ({ data }) => {
  const chartData = {
    labels: data.map((item) => item.date) || [],
    datasets: [
      {
        label: "Average Session Duration (minutes)",
        data: data.map((item) => item.avg_duration) || [],
        backgroundColor: "rgba(255, 205, 86, 0.6)",
        borderColor: "rgba(255, 205, 86, 1)",
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return <Bar data={chartData} options={options} />;
};

// Learning Outcomes Chart
export const LearningOutcomesChart = ({ data }) => {
  const chartData = {
    labels: data.map((item) => item.outcome) || [],
    datasets: [
      {
        label: "Students Achieving Outcome",
        data: data.map((item) => item.count) || [],
        backgroundColor: [
          "rgba(76, 175, 80, 0.6)",
          "rgba(33, 150, 243, 0.6)",
          "rgba(255, 193, 7, 0.6)",
          "rgba(156, 39, 176, 0.6)",
          "rgba(255, 87, 34, 0.6)",
        ],
        borderColor: [
          "rgba(76, 175, 80, 1)",
          "rgba(33, 150, 243, 1)",
          "rgba(255, 193, 7, 1)",
          "rgba(156, 39, 176, 1)",
          "rgba(255, 87, 34, 1)",
        ],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "right",
      },
    },
  };

  return <Doughnut data={chartData} options={options} />;
};

// Engagement Heatmap Chart
export const EngagementHeatmapChart = ({ data }) => {
  const chartData = {
    labels: data.hours || [],
    datasets: [
      {
        label: "Monday",
        data: data.monday || [],
        backgroundColor: "rgba(255, 99, 132, 0.6)",
      },
      {
        label: "Tuesday",
        data: data.tuesday || [],
        backgroundColor: "rgba(54, 162, 235, 0.6)",
      },
      {
        label: "Wednesday",
        data: data.wednesday || [],
        backgroundColor: "rgba(255, 205, 86, 0.6)",
      },
      {
        label: "Thursday",
        data: data.thursday || [],
        backgroundColor: "rgba(75, 192, 192, 0.6)",
      },
      {
        label: "Friday",
        data: data.friday || [],
        backgroundColor: "rgba(153, 102, 255, 0.6)",
      },
      {
        label: "Saturday",
        data: data.saturday || [],
        backgroundColor: "rgba(255, 159, 64, 0.6)",
      },
      {
        label: "Sunday",
        data: data.sunday || [],
        backgroundColor: "rgba(199, 199, 199, 0.6)",
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: "Hour of Day",
        },
      },
      y: {
        title: {
          display: true,
          text: "Day of Week",
        },
      },
    },
  };

  return <Bar data={chartData} options={options} />;
};

// Retention Rate Chart
export const RetentionRateChart = ({ data }) => {
  const chartData = {
    labels: data.map((item) => `Week ${item.week}`) || [],
    datasets: [
      {
        label: "Retention Rate (%)",
        data: data.map((item) => item.retention_rate) || [],
        borderColor: "rgba(75, 192, 192, 1)",
        backgroundColor: "rgba(75, 192, 192, 0.2)",
        tension: 0.1,
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        title: {
          display: true,
          text: "Retention Rate (%)",
        },
      },
      x: {
        title: {
          display: true,
          text: "Weeks Since Registration",
        },
      },
    },
  };

  return <Line data={chartData} options={options} />;
};
