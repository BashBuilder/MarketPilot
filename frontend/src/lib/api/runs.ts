import {
  ApproveRequestSchema,
  ApproveResponseSchema,
  ReviseRequestSchema,
  ReviseResponseSchema,
  type ApproveResponse,
  type ReviseRequest,
  type ReviseResponse,
} from "@/lib/schemas";
import { apiRequest } from "./client";

function runPath(runId: string): string {
  return `/runs/${encodeURIComponent(runId)}`;
}

export async function approveRun(
  runId: string,
  comment?: string,
  signal?: AbortSignal,
): Promise<ApproveResponse> {
  const body = ApproveRequestSchema.parse(comment === undefined ? {} : { comment });
  return apiRequest(`${runPath(runId)}/approve`, ApproveResponseSchema, {
    method: "POST",
    body,
    signal,
  });
}

export async function reviseRun(
  runId: string,
  input: ReviseRequest,
  signal?: AbortSignal,
): Promise<ReviseResponse> {
  const body = ReviseRequestSchema.parse(input);
  return apiRequest(`${runPath(runId)}/revise`, ReviseResponseSchema, {
    method: "POST",
    body,
    signal,
  });
}
