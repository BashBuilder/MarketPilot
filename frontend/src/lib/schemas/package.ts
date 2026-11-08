import { z } from "zod";

const TextSchema = z.string().min(1);
const TextListSchema = z.array(TextSchema);

export const BriefSchema = z.object({
  product: TextSchema,
  goal: TextSchema,
  audience: TextSchema,
  tone: TextSchema,
  channels: TextListSchema,
  constraints: TextListSchema,
});

export const ResearchSchema = z.object({
  segments: z.array(z.object({ name: TextSchema, description: TextSchema })),
  pain_points: TextListSchema,
  messaging_angles: TextListSchema,
  sources: z.array(z.object({ title: TextSchema, url: z.url() })),
});

export const CopySchema = z.object({
  variants: z.array(
    z.object({ channel: TextSchema, headline: TextSchema, description: TextSchema, cta: TextSchema }),
  ),
});

export const DirectionSchema = z.object({
  style_guide: TextSchema,
  composition: TextSchema,
  image_prompts: TextListSchema,
  video_prompts: TextListSchema,
  negative_prompts: TextListSchema,
});

export const AssetsSchema = z.object({
  assets: z.array(
    z.object({
      uri: TextSchema,
      checksum: z.string().regex(/^[a-f0-9]{64}$/i),
      model: TextSchema,
      // 64-bit seeds exceed Number.MAX_SAFE_INTEGER, so this must not enforce
      // the safe-integer cap (z.number().int() does).
      seed: z
        .number()
        .refine((value) => Number.isInteger(value) && value >= 0, "seed must be a non-negative integer"),
      prompt: TextSchema,
    }),
  ),
});

export const ComplianceSchema = z.object({
  items: z.array(z.object({ check: TextSchema, passed: z.boolean(), reason: TextSchema })),
});

const DimensionSchema = z.object({
  score: z.number().min(0).max(10),
  justification: z.string().min(5).max(200),
});

export const ScoreSchema = z.object({
  brief_alignment: DimensionSchema,
  audience_fit: DimensionSchema,
  copy_quality: DimensionSchema,
  visual_quality: DimensionSchema,
  compliance_risk: DimensionSchema,
  total: z.number().min(0).max(100),
});

// Sections are nullable *and* omittable: `response_model_exclude_none` may drop them.
export const CampaignPackageSchema = z.object({
  brief: BriefSchema.nullable().default(null),
  research: ResearchSchema.nullable().default(null),
  copy: CopySchema.nullable().default(null),
  direction: DirectionSchema.nullable().default(null),
  assets: AssetsSchema.nullable().default(null),
  compliance: ComplianceSchema.nullable().default(null),
  score: ScoreSchema.nullable().default(null),
});

export const SCORE_DIMENSIONS = [
  "brief_alignment",
  "audience_fit",
  "copy_quality",
  "visual_quality",
  "compliance_risk",
] as const;

export type Brief = z.infer<typeof BriefSchema>;
export type Research = z.infer<typeof ResearchSchema>;
export type AdCopy = z.infer<typeof CopySchema>;
export type CreativeDirection = z.infer<typeof DirectionSchema>;
export type AssetSet = z.infer<typeof AssetsSchema>;
export type ComplianceReport = z.infer<typeof ComplianceSchema>;
export type ScoreDimension = z.infer<typeof DimensionSchema>;
export type CreativeScore = z.infer<typeof ScoreSchema>;
export type CampaignPackage = z.infer<typeof CampaignPackageSchema>;
