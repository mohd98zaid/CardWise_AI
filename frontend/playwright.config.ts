import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  expect: {
    timeout: 10000,
  },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:5174",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "python -m uvicorn app.main:app --host 127.0.0.1 --port 8008",
      cwd: "../backend",
      env: {
        DATABASE_URL: "sqlite:///./test_browser_e2e.db",
        ALLOWED_ORIGINS: "http://localhost:5174,http://127.0.0.1:5174",
        AUTH_RATE_LIMIT: "1000",
      },
      url: "http://127.0.0.1:8008/ready",
      reuseExistingServer: false,
      timeout: 30000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5174",
      cwd: ".",
      env: {
        VITE_API_BASE_URL: "http://127.0.0.1:8008",
      },
      url: "http://127.0.0.1:5174",
      reuseExistingServer: false,
      timeout: 30000,
    },
  ],
});
