import { z } from "zod";

export const ApiErrorCodeSchema = z.string().min(1);

export const ApiErrorEnvelopeSchema = z.object({
  error: z.object({
    code: ApiErrorCodeSchema,
    message: z.string().min(1),
    details: z.unknown().optional(),
  }),
});

export type ApiErrorCode = z.infer<typeof ApiErrorCodeSchema>;
export type ApiErrorEnvelope = z.infer<typeof ApiErrorEnvelopeSchema>;

export const CLIENT_ERROR_CODES = {
  network: "network_error",
  invalidResponse: "invalid_response",
  unexpected: "unexpected_error",
} as const;
