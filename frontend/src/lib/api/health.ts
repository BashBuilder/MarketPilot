import { z } from "zod";
import { apiRequest } from "./client";

// The contract only guarantees a 200; the body is not part of section 2.
const HealthSchema = z.unknown();

export async function checkHealth(signal?: AbortSignal): Promise<void> {
  await apiRequest("/health", HealthSchema, { signal });
}
