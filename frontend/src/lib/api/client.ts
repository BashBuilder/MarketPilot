import type { z } from "zod";
import { ApiErrorEnvelopeSchema, CLIENT_ERROR_CODES } from "@/lib/schemas";

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

function resolveBaseUrl(): string {
  // In the browser, mock mode runs same-origin so the service worker can
  // intercept every call. On the server, an absolute URL is required; the Node
  // MSW server matches handlers by path, so the configured base still works.
  if (typeof window !== "undefined" && process.env.NEXT_PUBLIC_API_MOCKING === "enabled") {
    return "/api/v1";
  }
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  const base = configured && configured.length > 0 ? configured : DEFAULT_API_BASE_URL;
  return base.replace(/\/+$/, "");
}

export const API_BASE_URL = resolveBaseUrl();

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }

  get isNetworkError(): boolean {
    return this.status === 0;
  }
}

export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError;
}

export interface ApiRequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

function buildUrl(path: string): string {
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (text.length === 0) return undefined;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return undefined;
  }
}

export async function apiRequest<T>(
  path: string,
  schema: z.ZodType<T>,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { method = "GET", body, headers, signal } = options;

  let response: Response;
  try {
    response = await fetch(buildUrl(path), {
      method,
      cache: "no-store",
      signal,
      headers: body === undefined ? headers : { "Content-Type": "application/json", ...headers },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === "AbortError") throw cause;
    throw new ApiError(
      0,
      CLIENT_ERROR_CODES.network,
      "Could not reach the MarketPilot API. Check your connection and try again.",
    );
  }

  const payload = await readJson(response);

  if (!response.ok) {
    const parsed = ApiErrorEnvelopeSchema.safeParse(payload);
    if (parsed.success) {
      throw new ApiError(
        response.status,
        parsed.data.error.code,
        parsed.data.error.message,
        parsed.data.error.details,
      );
    }
    throw new ApiError(
      response.status,
      `http_${response.status}`,
      `The API request failed with status ${response.status}.`,
    );
  }

  const parsed = schema.safeParse(payload);
  if (!parsed.success) {
    throw new ApiError(
      response.status,
      CLIENT_ERROR_CODES.invalidResponse,
      "The API returned a response this app does not understand.",
      parsed.error.issues,
    );
  }
  return parsed.data;
}
