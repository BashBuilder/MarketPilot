import { z } from "zod";

export const CAMPAIGN_STATUSES = [
  "draft",
  "running",
  "awaiting_approval",
  "completed",
  "failed",
] as const;

export const CampaignStatusSchema = z.enum(CAMPAIGN_STATUSES);

export const CampaignSummarySchema = z.object({
  id: z.string().min(1),
  idea: z.string().min(1),
  status: CampaignStatusSchema,
  latest_version: z.number().int().nonnegative().nullable(),
  latest_score: z.number().min(0).max(100).nullable(),
  active_run_id: z.string().min(1).nullable(),
  created_at: z.string().min(1),
  updated_at: z.string().min(1),
});

export const CampaignSummaryListSchema = z.array(CampaignSummarySchema);

export const MAX_IDEA_LENGTH = 2000;

export const CreateCampaignRequestSchema = z.object({
  idea: z.string().trim().min(1).max(MAX_IDEA_LENGTH),
});

export const CreateCampaignResponseSchema = z.object({
  campaign_id: z.string().min(1),
  run_id: z.string().min(1),
});

export type CampaignStatus = z.infer<typeof CampaignStatusSchema>;
export type CampaignSummary = z.infer<typeof CampaignSummarySchema>;
export type CreateCampaignRequest = z.infer<typeof CreateCampaignRequestSchema>;
export type CreateCampaignResponse = z.infer<typeof CreateCampaignResponseSchema>;
