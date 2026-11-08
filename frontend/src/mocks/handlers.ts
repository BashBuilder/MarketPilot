import { delay, http, HttpResponse } from "msw";
import { CreateCampaignRequestSchema, ReviseRequestSchema } from "@/lib/schemas";
import { mirrorCampaign } from "./bridge";
import { buildCompletedScript, buildRunScript, type ScriptStep } from "./fixtures/sse";
import { approveMockRun, createMockCampaign, reviseMockRun } from "./run-actions";
import { mockStore } from "./store";

const BASE = "*/api/v1";

function errorResponse(status: number, code: string, message: string) {
  return HttpResponse.json({ error: { code, message } }, { status });
}

function sseStream(steps: ScriptStep[], lastEventId: string | null): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  const last = Number(lastEventId ?? "0");
  const remaining = steps.filter((step) => Number(step.event.id) > last);

  return new ReadableStream({
    async start(controller) {
      for (const step of remaining) {
        const { id, event, data } = step.event;
        controller.enqueue(
          encoder.encode(`id: ${id}\nevent: ${event}\ndata: ${JSON.stringify(data)}\n\n`),
        );
        await delay(step.delayMs);
      }
      controller.close();
    },
  });
}

export const handlers = [
  http.get(`${BASE}/health`, () => HttpResponse.json({ status: "ok" })),

  http.get(`${BASE}/campaigns`, () => HttpResponse.json(mockStore.listCampaigns())),

  http.post(`${BASE}/campaigns`, async ({ request }) => {
    const parsed = CreateCampaignRequestSchema.safeParse(await request.json().catch(() => null));
    if (!parsed.success) {
      return errorResponse(422, "validation_error", "idea must be between 1 and 2000 characters");
    }
    const created = createMockCampaign(parsed.data.idea);
    void mirrorCampaign({
      idea: parsed.data.idea,
      campaignId: created.campaign_id,
      runId: created.run_id,
    });
    return HttpResponse.json(created, { status: 201 });
  }),

  http.get(`${BASE}/campaigns/:id`, ({ params }) => {
    const campaign = mockStore.getCampaign(String(params.id));
    if (!campaign) return errorResponse(404, "not_found", "Campaign not found");
    return HttpResponse.json(campaign);
  }),

  http.get(`${BASE}/campaigns/:id/versions`, ({ params }) => {
    const campaign = mockStore.getCampaign(String(params.id));
    if (!campaign) return errorResponse(404, "not_found", "Campaign not found");
    return HttpResponse.json(mockStore.listVersions(campaign.id));
  }),

  http.get(`${BASE}/campaigns/:id/versions/:version`, ({ params }) => {
    const pkg = mockStore.getPackage(String(params.id), Number(params.version));
    if (!pkg) return errorResponse(404, "not_found", "Version not found");
    return HttpResponse.json(pkg);
  }),

  http.get(`${BASE}/campaigns/:id/versions/:from/diff/:to`, ({ params }) => {
    const diff = mockStore.getDiff(String(params.id), Number(params.from), Number(params.to));
    if (!diff) return errorResponse(404, "not_found", "No diff between those versions");
    return HttpResponse.json(diff);
  }),

  http.post(`${BASE}/runs/:id/approve`, async ({ params, request }) => {
    const run = mockStore.getRun(String(params.id));
    if (!run) return errorResponse(404, "not_found", "Run not found");
    if (run.status !== "awaiting_approval") {
      return errorResponse(409, "run_not_awaiting_approval", "Run is not awaiting approval");
    }
    const body = (await request.json().catch(() => ({}))) as { comment?: string };
    const approved = approveMockRun(run.id, body.comment);
    if (!approved) return errorResponse(404, "not_found", "Run not found");
    return HttpResponse.json(approved);
  }),

  http.post(`${BASE}/runs/:id/revise`, async ({ params, request }) => {
    const parsed = ReviseRequestSchema.safeParse(await request.json().catch(() => null));
    if (!parsed.success) return errorResponse(422, "validation_error", "comment is required");
    const revised = reviseMockRun(String(params.id), parsed.data);
    if (!revised) return errorResponse(404, "not_found", "Run not found");
    return HttpResponse.json(revised);
  }),

  http.get(`${BASE}/runs/:id/stream`, ({ params, request }) => {
    const run = mockStore.getRun(String(params.id));
    if (!run) return errorResponse(404, "not_found", "Run not found");

    const steps =
      run.status === "completed"
        ? buildCompletedScript(run.id, run.version ?? 1, null)
        : buildRunScript(run.id, run.version ?? 1);

    return new HttpResponse(sseStream(steps, request.headers.get("Last-Event-ID")), {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  }),

  http.all(`${BASE}/*`, ({ request }) =>
    errorResponse(404, "not_found", `No mock handler for ${request.method} ${new URL(request.url).pathname}`),
  ),
];
