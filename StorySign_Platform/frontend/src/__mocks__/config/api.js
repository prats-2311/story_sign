/**
 * Mock API Configuration for Tests
 */

export const getApiConfig = () => ({
  API_BASE_URL: "http://localhost:8000",
  WS_BASE_URL: "ws://localhost:8000",
  API_VERSION: "v1",
});

export const buildApiUrl = (path) => `http://localhost:8000/api/v1${path}`;

export const buildWsUrl = (path) => `ws://localhost:8000${path}`;

export const buildHealthCheckUrl = () => "http://localhost:8000/health";

export const getEnvironmentInfo = () => ({
  NODE_ENV: "test",
  API_BASE_URL: "http://localhost:8000",
  WS_BASE_URL: "ws://localhost:8000",
  API_VERSION: "v1",
  USE_PROXY: false,
});

export default getApiConfig();
