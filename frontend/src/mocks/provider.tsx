"use client";

import { useEffect, type ReactNode } from "react";
import { isMockingEnabled } from "./is-mocking-enabled";

// One worker per page: React's dev double-effect must not call start() twice.
let startPromise: Promise<void> | null = null;

function startWorker(): Promise<void> {
  // Imported lazily so the server graph never evaluates the browser worker.
  startPromise ??= import("./browser").then(async ({ worker }) => {
    await worker.start({ quiet: true });
  });
  return startPromise;
}

/**
 * Starts the browser mock worker. Server Components are served by the Node MSW
 * server in `instrumentation.ts`, so children render normally on the server and
 * client mutations wait for user interaction, by which point the worker runs.
 */
export function MockProvider({ children }: { children: ReactNode }) {
  const enabled = isMockingEnabled();

  useEffect(() => {
    if (!enabled) return;
    void startWorker().catch((error: unknown) => {
      console.error("Mock worker failed to start", error);
    });
  }, [enabled]);

  return <>{children}</>;
}
