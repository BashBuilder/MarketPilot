import { describe, expect, it } from "vitest";
import { ApiErrorEnvelopeSchema } from "./api-error";

describe("ApiErrorEnvelopeSchema", () => {
  it("accepts an error with details", () => {
    const envelope = {
      error: {
        code: "too_many_runs",
        message: "Too many runs in flight",
        details: { limit: 3 },
      },
    };
    expect(ApiErrorEnvelopeSchema.parse(envelope)).toEqual(envelope);
  });

  it("accepts an error without details", () => {
    expect(
      ApiErrorEnvelopeSchema.parse({ error: { code: "not_found", message: "No such campaign" } })
        .error.code,
    ).toBe("not_found");
  });

  it("rejects a missing message", () => {
    expect(() => ApiErrorEnvelopeSchema.parse({ error: { code: "not_found" } })).toThrow();
  });

  it("rejects an unwrapped message", () => {
    expect(() => ApiErrorEnvelopeSchema.parse({ message: "Not found" })).toThrow();
  });
});
