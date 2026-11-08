import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { approveRun, reviseRun } from "./runs";
import { checkHealth } from "./health";

const server = setupServer();
const runId = "11111111-1111-4111-8111-111111111111";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("run endpoints", () => {
  it("approves a run with an optional comment", async () => {
    let received: unknown;
    server.use(
      http.post(`*/api/v1/runs/${runId}/approve`, async ({ request }) => {
        received = await request.json();
        return HttpResponse.json({ status: "completed", version: 1 });
      }),
    );

    await expect(approveRun(runId, "Looks good")).resolves.toEqual({
      status: "completed",
      version: 1,
    });
    expect(received).toEqual({ comment: "Looks good" });
  });

  it("revises a run and returns the continuation run", async () => {
    let received: unknown;
    server.use(
      http.post(`*/api/v1/runs/${runId}/revise`, async ({ request }) => {
        received = await request.json();
        return HttpResponse.json({ run_id: "run-2", version: 2 });
      }),
    );

    await expect(
      reviseRun(runId, { comment: "Sharper headline", target_node: "copywriter" }),
    ).resolves.toEqual({ run_id: "run-2", version: 2 });
    expect(received).toEqual({ comment: "Sharper headline", target_node: "copywriter" });
  });

  it("rejects a revise call without a comment before calling the API", async () => {
    await expect(reviseRun(runId, { comment: "  " })).rejects.toThrow();
  });

  it("surfaces a backend 429 with its code", async () => {
    server.use(
      http.post(`*/api/v1/runs/${runId}/approve`, () =>
        HttpResponse.json(
          { error: { code: "too_many_runs", message: "Too many runs in flight" } },
          { status: 429 },
        ),
      ),
    );

    await expect(approveRun(runId)).rejects.toMatchObject({
      status: 429,
      code: "too_many_runs",
    });
  });
});

describe("health endpoint", () => {
  it("resolves when the API is healthy", async () => {
    server.use(http.get("*/api/v1/health", () => HttpResponse.json({ status: "ok" })));
    await expect(checkHealth()).resolves.toBeUndefined();
  });
});
