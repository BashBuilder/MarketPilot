import { z } from "zod";
import { AgentSchema } from "./sse-events";

export const VersionSummarySchema = z.object({
  version: z.number().int().positive(),
  parent_version_id: z.string().min(1).nullable(),
  score: z.number().min(0).max(100).nullable(),
  created_at: z.string().min(1),
});

export const VersionSummaryListSchema = z.array(VersionSummarySchema);

export const DiffChangeSchema = z.object({
  path: z.string().min(1),
  before: z.unknown(),
  after: z.unknown(),
});

export const VersionDiffSchema = z.object({
  from: z.number().int().positive(),
  to: z.number().int().positive(),
  changes: z.array(DiffChangeSchema),
});

export const ApproveRequestSchema = z.object({
  comment: z.string().max(2000).optional(),
});

export const ApproveResponseSchema = z.object({
  status: z.literal("completed"),
  version: z.number().int().positive(),
});

export const ReviseRequestSchema = z.object({
  comment: z.string().trim().min(1).max(2000),
  target_node: AgentSchema.optional(),
});

export const ReviseResponseSchema = z.object({
  run_id: z.string().min(1),
  version: z.number().int().positive(),
});

export type VersionSummary = z.infer<typeof VersionSummarySchema>;
export type DiffChange = z.infer<typeof DiffChangeSchema>;
export type VersionDiff = z.infer<typeof VersionDiffSchema>;
export type ApproveRequest = z.infer<typeof ApproveRequestSchema>;
export type ApproveResponse = z.infer<typeof ApproveResponseSchema>;
export type ReviseRequest = z.infer<typeof ReviseRequestSchema>;
export type ReviseResponse = z.infer<typeof ReviseResponseSchema>;
