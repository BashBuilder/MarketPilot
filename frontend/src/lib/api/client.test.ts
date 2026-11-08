import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { z } from "zod";
import { ApiError, apiRequest, isApiError } from "./client";

const server = setupServer();
const ThingSchema = z.object({ id: z.string().min(1), count: z.number() });

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("apiRequest", () => {
  it("parses a successful response with its schema", async () => {
    server.use(
      http.get("*/api/v1/things", () => HttpResponse.json({ id: "thing-1", count: 2 })),
    );

    await expect(apiRequest("/things", ThingSchema)).resolves.toEqual({ id: "thing-1", count: 2 });
  });

  it("throws invalid_response when the payload breaks the schema", async () => {
    server.use(http.get("*/api/v1/things", () => HttpResponse.json({ id: "thing-1" })));

    const error = await apiRequest("/things", ThingSchema).catch((cause: unknown) => cause);

    expect(isApiError(error)).toBe(true);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe("invalid_response");
    expect((error as ApiError).status).toBe(200);
  });

  it("throws a typed ApiError using the backend error envelope", async () => {
    server.use(
      http.get("*/api/v1/things", () =>
        HttpResponse.json(
          { error: { code: "not_found", message: "No such thing", details: { id: "thing-1" } } },
          { status: 404 },
        ),
      ),
    );

    const error = (await apiRequest("/things", ThingSchema).catch((cause: unknown) => cause)) as ApiError;

    expect(error.code).toBe("not_found");
    expect(error.message).toBe("No such thing");
    expect(error.status).toBe(404);
    expect(error.details).toEqual({ id: "thing-1" });
  });

  it("falls back to an http_<status> code when the body is not an envelope", async () => {
    server.use(http.get("*/api/v1/things", () => new HttpResponse("boom", { status: 500 })));

    const error = (await apiRequest("/things", ThingSchema).catch((cause: unknown) => cause)) as ApiError;

    expect(error.code).toBe("http_500");
  });

  it("reports a network failure as status 0", async () => {
    server.use(http.get("*/api/v1/things", () => HttpResponse.error()));

    const error = (await apiRequest("/things", ThingSchema).catch((cause: unknown) => cause)) as ApiError;

    expect(error.code).toBe("network_error");
    expect(error.isNetworkError).toBe(true);
  });

  it("sends a JSON body with the POST method", async () => {
    let received: unknown;
    server.use(
      http.post("*/api/v1/things", async ({ request }) => {
        received = await request.json();
        return HttpResponse.json({ id: "thing-1", count: 1 }, { status: 201 });
      }),
    );

    await apiRequest("/things", ThingSchema, { method: "POST", body: { id: "thing-1", count: 1 } });

    expect(received).toEqual({ id: "thing-1", count: 1 });
  });
});
