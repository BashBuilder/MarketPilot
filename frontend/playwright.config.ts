import { defineConfig, devices } from "@playwright/test";

// The `real` project only runs against a backend at E2E_API_URL and is
// skipped (not failed) when the variable is unset.
const realApiUrl = process.env.E2E_API_URL;
const realEnabled = Boolean(realApiUrl);

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? "github" : "list",
  use: {
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "mock",
      testIgnore: /real\..*\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        baseURL: "http://localhost:3000",
      },
    },
    ...(realEnabled
      ? [
          {
            name: "real",
            testMatch: /real\..*\.spec\.ts/,
            use: {
              ...devices["Desktop Chrome"],
              baseURL: "http://localhost:3001",
            },
          },
        ]
      : []),
  ],
  webServer: [
    {
      command: "pnpm dev:mock",
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
      env: { NEXT_PUBLIC_API_MOCKING: "enabled" },
    },
    ...(realEnabled
      ? [
          {
            command: "pnpm dev --port 3001",
            url: "http://localhost:3001",
            reuseExistingServer: !process.env.CI,
            env: {
              NEXT_PUBLIC_API_URL: realApiUrl as string,
              NEXT_PUBLIC_API_MOCKING: "disabled",
            },
          },
        ]
      : []),
  ],
});
