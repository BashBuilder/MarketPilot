import { NextResponse } from "next/server";
import { z } from "zod";
import { CreateCampaignRequestSchema } from "@/lib/schemas";
import { createMockCampaign } from "@/mocks/run-actions";
import { mockStore } from "@/mocks/store";

const MirrorBodySchema = CreateCampaignRequestSchema.extend({
  campaign_id: z.string().min(1).optional(),
  run_id: z.string().min(1).optional(),
});

function disabled(): NextResponse {
  return NextResponse.json(
    { error: { code: "not_found", message: "Mock API is disabled" } },
    { status: 404 },
  );
}

export async function GET(): Promise<NextResponse> {
  if (process.env.NEXT_PUBLIC_API_MOCKING !== "enabled") return disabled();
  return NextResponse.json(mockStore.listCampaigns());
}

export async function POST(request: Request): Promise<NextResponse> {
  if (process.env.NEXT_PUBLIC_API_MOCKING !== "enabled") return disabled();

  const parsed = MirrorBodySchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: "validation_error", message: "idea is required" } },
      { status: 422 },
    );
  }

  const { idea, campaign_id: campaignId, run_id: runId } = parsed.data;
  const created = createMockCampaign(idea, { campaignId, runId });
  return NextResponse.json(created, { status: 201 });
}
