import { z } from "zod";

export const AGENTS = [
  "brief",
  "research",
  "copywriter",
  "creative_director",
  "designer",
  "compliance",
  "reviewer",
  "supervisor",
] as const;

export const AgentSchema = z.enum(AGENTS);
export const StreamActorSchema = z.enum([...AGENTS, "human"]);

const BaseDataSchema = z.object({
  run_id: z.string().min(1),
  timestamp: z.string().min(1),
  agent: StreamActorSchema,
});

const idField = z.string().min(1);

const AgentStartedEventSchema = z.object({
  id: idField, event: z.literal("agent_started"), data: BaseDataSchema,
});

const AgentHandoffEventSchema = z.object({
  id: idField, event: z.literal("agent_handoff"),
  data: BaseDataSchema.extend({ from: StreamActorSchema, to: StreamActorSchema }),
});

const ToolCalledEventSchema = z.object({
  id: idField, event: z.literal("tool_called"),
  data: BaseDataSchema.extend({
    tool: z.string().min(1),
    duration_ms: z.number().int().nonnegative(),
    status: z.enum(["success", "error", "denied"]),
  }),
});

const ValidationFailedEventSchema = z.object({
  id: idField, event: z.literal("validation_failed"),
  data: BaseDataSchema.extend({ reason: z.string().min(1) }),
});

const RetryingEventSchema = z.object({
  id: idField, event: z.literal("retrying"),
  data: BaseDataSchema.extend({
    attempt: z.number().int().positive(),
    max_attempts: z.number().int().positive(),
  }),
});

const AwaitingApprovalEventSchema = z.object({
  id: idField, event: z.literal("awaiting_approval"),
  data: BaseDataSchema.extend({ version: z.number().int().positive() }),
});

const CompletedEventSchema = z.object({
  id: idField, event: z.literal("completed"),
  data: BaseDataSchema.extend({
    version: z.number().int().positive(),
    score: z.number().min(0).max(100).nullable(),
  }),
});

const ErrorEventSchema = z.object({
  id: idField, event: z.literal("error"),
  data: BaseDataSchema.extend({ message: z.string().min(1), recoverable: z.boolean() }),
});

export const SseEventSchema = z.discriminatedUnion("event", [
  AgentStartedEventSchema,
  AgentHandoffEventSchema,
  ToolCalledEventSchema,
  ValidationFailedEventSchema,
  RetryingEventSchema,
  AwaitingApprovalEventSchema,
  CompletedEventSchema,
  ErrorEventSchema,
]);

export function isTerminalEvent(parsed: SseEvent): boolean {
  if (parsed.event === "error") return !parsed.data.recoverable;
  return parsed.event === "awaiting_approval" || parsed.event === "completed";
}

export type Agent = z.infer<typeof AgentSchema>;
export type StreamActor = z.infer<typeof StreamActorSchema>;
export type SseEvent = z.infer<typeof SseEventSchema>;
export type SseEventType = SseEvent["event"];
